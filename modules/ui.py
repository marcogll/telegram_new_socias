from telegram import ReplyKeyboardMarkup


def main_actions_keyboard() -> ReplyKeyboardMarkup:
    """Teclado inferior con comandos directos (un toque lanza el flujo)."""
    return ReplyKeyboardMarkup(
        [
            ["/welcome"],
            ["/vacaciones", "/permiso"],
            ["/links", "/start"],
        ],
        resize_keyboard=True,
    )
