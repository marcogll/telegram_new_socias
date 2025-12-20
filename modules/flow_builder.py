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

# Assuming finalization logic will be handled elsewhere for now
# from .onboarding import finalizar, cancelar

# A simple end state for now
async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Flow ended.")
    return ConversationHandler.END

async def generic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict):
    current_state_key = context.user_data.get("current_state", 0)
    
    # Find the current step in the flow
    current_step = next((step for step in flow["steps"] if step["state"] == current_state_key), None)
    
    if not current_step:
        await update.message.reply_text("Hubo un error en el flujo. Por favor, inicia de nuevo.")
        return ConversationHandler.END

    # Save the answer
    user_answer = update.message.text
    variable_name = current_step.get("variable")
    if variable_name:
        context.user_data[variable_name] = user_answer

    # Determine the next state
    next_state_key = None
    if "next_steps" in current_step:
        for condition in current_step["next_steps"]:
            if condition["value"] == user_answer:
                next_state_key = condition["go_to"]
                break
            elif condition["value"] == "default":
                next_state_key = condition["go_to"]
    elif "next_step" in current_step:
        next_state_key = current_step["next_step"]

    if next_state_key is None:
        # If no next step is defined, end the conversation
        return await end(update, context)

    # Find the next step
    next_step = next((step for step in flow["steps"] if step["state"] == next_state_key), None)

    if not next_step:
        # If the next step is the end of the conversation
        if next_state_key == -1:
            # Here we would call the generic "finalizar" function
            # For now, just end it
            await update.message.reply_text("Has completado el flujo. ¡Gracias!")
            # return await finalizar(update, context)
            return ConversationHandler.END
        else:
            await update.message.reply_text("Error: No se encontró el siguiente paso del flujo.")
            return ConversationHandler.END

    # Ask the next question
    reply_markup = ReplyKeyboardRemove()
    if next_step.get("type") == "keyboard" and "options" in next_step:
        reply_markup = ReplyKeyboardMarkup(
            [next_step["options"][i:i+3] for i in range(0, len(next_step["options"]), 3)],
            one_time_keyboard=True, resize_keyboard=True
        )

    await update.message.reply_text(next_step["question"], reply_markup=reply_markup)

    # Update the current state
    context.user_data["current_state"] = next_state_key
    return next_state_key


async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict):
    context.user_data.clear()
    context.user_data["flow_name"] = flow["flow_name"]
    
    # Start with the first step
    first_step = flow["steps"][0]
    context.user_data["current_state"] = first_step["state"]

    reply_markup = ReplyKeyboardRemove()
    if first_step.get("type") == "keyboard" and "options" in first_step:
        reply_markup = ReplyKeyboardMarkup(
            [first_step["options"][i:i+3] for i in range(0, len(first_step["options"]), 3)],
            one_time_keyboard=True, resize_keyboard=True
        )
        
    await update.message.reply_text(first_step["question"], reply_markup=reply_markup)
    return first_step["state"]


def create_handler(flow: dict):
    states = {}
    for step in flow["steps"]:
        callback = partial(generic_callback, flow=flow)
        states[step["state"]] = [MessageHandler(filters.TEXT & ~filters.COMMAND, callback)]

    # The entry point should be a command with the same name as the flow
    entry_point = CommandHandler(flow["flow_name"], partial(start_flow, flow=flow))

    return ConversationHandler(
        entry_points=[entry_point],
        states=states,
        fallbacks=[CommandHandler("cancelar", end)], # Replace with generic cancel
        allow_reentry=True,
    )

def load_flows():
    flow_handlers = []
    for filename in os.listdir("conv-flows"):
        if filename.endswith(".json"):
            filepath = os.path.join("conv-flows", filename)
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
