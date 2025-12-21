import ast
import json
import logging
import os
from functools import partial

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from .finalizer import finalize_flow


def _build_keyboard(options):
    keyboard = [options[i : i + 2] for i in range(0, len(options), 2)]
    return ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True,
    )


def _preprocess_flow(flow: dict):
    """Populate missing next_step values assuming a linear order."""
    steps = flow.get("steps", [])
    for idx, step in enumerate(steps):
        if "next_step" in step or "next_steps" in step:
            continue
        if idx + 1 < len(steps):
            step["next_step"] = steps[idx + 1]["state"]
        else:
            step["next_step"] = -1


def _find_step(flow: dict, state_key):
    return next((step for step in flow["steps"] if step["state"] == state_key), None)


ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.Compare,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.List,
    ast.Tuple,
    ast.And,
    ast.Or,
    ast.Eq,
    ast.NotEq,
    ast.In,
    ast.NotIn,
)


def _evaluate_condition(condition: str, response: str) -> bool:
    """Safely evaluate expressions like `response in ['Hoy', 'Mañana']`."""
    if not condition:
        return False
    try:
        tree = ast.parse(condition, mode="eval")
        for node in ast.walk(tree):
            if not isinstance(node, ALLOWED_AST_NODES):
                raise ValueError(f"Unsupported expression: {condition}")
        compiled = compile(tree, "<condition>", "eval")
        return bool(eval(compiled, {"__builtins__": {}}, {"response": response}))
    except Exception as exc:
        logging.warning("Failed to evaluate condition '%s': %s", condition, exc)
        return False


def _determine_next_state(step: dict, user_answer: str):
    """Resolve the next state declared in the JSON step."""
    if "next_steps" in step:
        default_target = None
        for option in step["next_steps"]:
            value = option.get("value")
            if value == "default":
                default_target = option.get("go_to")
            elif user_answer == value:
                return option.get("go_to")
        return default_target

    next_step = step.get("next_step")

    if isinstance(next_step, list):
        default_target = None
        for option in next_step:
            condition = option.get("condition")
            target = option.get("state")
            if condition:
                if _evaluate_condition(condition, user_answer):
                    return target
            elif option.get("value") and user_answer == option["value"]:
                return target
            elif option.get("default"):
                default_target = target
        return default_target

    return next_step


async def _go_to_state(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict, state_key):
    """Send the question for the requested state, skipping info-only steps."""
    safety_counter = 0
    while True:
        safety_counter += 1
        if safety_counter > len(flow["steps"]) + 2:
            logging.error("Detected potential loop while traversing flow '%s'", flow.get("flow_name"))
            await update.message.reply_text("Ocurrió un error al continuar con el flujo. Intenta iniciar de nuevo.")
            return ConversationHandler.END

        if state_key == -1:
            await finalize_flow(update, context)
            return ConversationHandler.END

        next_step = _find_step(flow, state_key)
        if not next_step:
            await update.message.reply_text("Error: No se encontró el siguiente paso del flujo.")
            return ConversationHandler.END

        reply_markup = ReplyKeyboardRemove()
        if next_step.get("type") == "keyboard" and "options" in next_step:
            reply_markup = _build_keyboard(next_step["options"])

        await update.message.reply_text(next_step["question"], reply_markup=reply_markup)
        context.user_data["current_state"] = state_key

        if next_step.get("type") == "info":
            state_key = _determine_next_state(next_step, None)
            if state_key is None:
                await update.message.reply_text("No se pudo continuar con el flujo actual. Intenta iniciar de nuevo.")
                return ConversationHandler.END
            continue

        return state_key


def create_handler(flow: dict):
    states = {}
    all_states = sorted(list(set([step["state"] for step in flow["steps"]])))
    for state_key in all_states:
        if state_key == -1:
            continue
        callback = partial(generic_callback, flow=flow)
        states[state_key] = [MessageHandler(filters.TEXT & ~filters.COMMAND, callback)]

    entry_point = CommandHandler(flow["flow_name"], partial(start_flow, flow=flow))

    return ConversationHandler(
        entry_points=[entry_point],
        states=states,
        fallbacks=[CommandHandler("cancelar", end_cancel)],
        allow_reentry=True,
    )


async def end_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Flujo cancelado.")
    return ConversationHandler.END


async def generic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict):
    current_state_key = context.user_data.get("current_state", 0)
    current_step = _find_step(flow, current_state_key)

    if not current_step:
        await update.message.reply_text("Hubo un error en el flujo. Por favor, inicia de nuevo.")
        return ConversationHandler.END

    user_answer = update.message.text
    variable_name = current_step.get("variable")
    if variable_name:
        context.user_data[variable_name] = user_answer

    next_state_key = _determine_next_state(current_step, user_answer)
    if next_state_key is None:
        return await end_cancel(update, context)

    return await _go_to_state(update, context, flow, next_state_key)


async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict):
    context.user_data.clear()
    context.user_data["flow_name"] = flow["flow_name"]

    first_state = flow["steps"][0]["state"]
    return await _go_to_state(update, context, flow, first_state)


def load_flows():
    flow_handlers = []
    flow_dir = "conv-flows"
    if not os.path.isdir(flow_dir):
        logging.warning(f"Directory not found: {flow_dir}")
        return flow_handlers

    for filename in os.listdir(flow_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(flow_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    flow_definition = json.load(f)
                    _preprocess_flow(flow_definition)
                    handler = create_handler(flow_definition)
                    flow_handlers.append(handler)
                    logging.info(f"Flow '{flow_definition['flow_name']}' loaded successfully.")
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from {filename}: {e}")
                except Exception as e:
                    logging.error(f"Error creating handler for {filename}: {e}")
    return flow_handlers
