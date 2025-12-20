import json
import os
import logging
from functools import partial
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    filters,
)

from .finalizer import finalize_flow

async def end_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Flujo cancelado.")
    return ConversationHandler.END

async def generic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict):
    current_state_key = context.user_data.get("current_state", 0)
    
    current_step = next((step for step in flow["steps"] if step["state"] == current_state_key), None)
    
    if not current_step:
        await update.message.reply_text("Hubo un error en el flujo. Por favor, inicia de nuevo.")
        return ConversationHandler.END

    user_answer = update.message.text
    variable_name = current_step.get("variable")
    if variable_name:
        context.user_data[variable_name] = user_answer

    next_state_key = None
    if "next_steps" in current_step:
        for condition in current_step["next_steps"]:
            if condition.get("value") == user_answer:
                next_state_key = condition["go_to"]
                break
            elif condition.get("value") == "default":
                next_state_key = condition["go_to"]
    elif "next_step" in current_step:
        next_state_key = current_step["next_step"]

    if next_state_key is None:
        return await end_cancel(update, context)

    if next_state_key == -1:
        await finalize_flow(update, context)
        return ConversationHandler.END

    next_step = next((step for step in flow["steps"] if step["state"] == next_state_key), None)

    if not next_step:
        await update.message.reply_text("Error: No se encontró el siguiente paso del flujo.")
        return ConversationHandler.END

    reply_markup = ReplyKeyboardRemove()
    if next_step.get("type") == "keyboard" and "options" in next_step:
        # Create a 2D array for the keyboard
        options = next_step["options"]
        keyboard = [options[i:i+2] for i in range(0, len(options), 2)]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True, resize_keyboard=True
        )

    await update.message.reply_text(next_step["question"], reply_markup=reply_markup)

    context.user_data["current_state"] = next_state_key
    return next_state_key


async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict):
    context.user_data.clear()
    context.user_data["flow_name"] = flow["flow_name"]
    
    first_step = flow["steps"][0]
    context.user_data["current_state"] = first_step["state"]

    reply_markup = ReplyKeyboardRemove()
    if first_step.get("type") == "keyboard" and "options" in first_step:
        options = first_step["options"]
        keyboard = [options[i:i+2] for i in range(0, len(options), 2)]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True, resize_keyboard=True
        )
        
    await update.message.reply_text(first_step["question"], reply_markup=reply_markup)
    return first_step["state"]


def create_handler(flow: dict):
    states = {}
    all_states = sorted(list(set([step["state"] for step in flow["steps"]])))
    
    for state_key in all_states:
        # Skip the end state
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
                    handler = create_handler(flow_definition)
                    flow_handlers.append(handler)
                    logging.info(f"Flow '{flow_definition['flow_name']}' loaded successfully.")
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from {filename}: {e}")
                except Exception as e:
                    logging.error(f"Error creating handler for {filename}: {e}")
    return flow_handlers
