import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

logger = logging.getLogger(__name__)

router = Router()

DONATE_AMOUNTS = {100, 200, 500}


@router.callback_query(F.data.startswith("donate:") & ~F.data.endswith("cancel"))
async def handle_donate(callback: CallbackQuery) -> None:
    amount = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    if amount not in DONATE_AMOUNTS:
        await callback.answer("Неверная сумма.", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer_invoice(  # type: ignore[union-attr]
        title="Поддержка бота",
        description=f"Донат {amount} ⭐ на развитие бота",
        prices=[LabeledPrice(label="Донат", amount=amount)],
        payload=f"donate_{amount}",
        currency="XTR",
    )
    await callback.answer()


@router.callback_query(F.data == "donate:cancel")
async def handle_donate_cancel(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Окей, в другой раз! 😊")  # type: ignore[union-attr]
    await callback.answer()


@router.pre_checkout_query()
async def handle_pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message) -> None:
    amount = message.successful_payment.total_amount  # type: ignore[union-attr]
    logger.info(
        "Donation received: %d stars from user %s",
        amount,
        message.from_user.id,  # type: ignore[union-attr]
    )
    await message.answer(
        f"🎉 Спасибо за донат {amount} ⭐!\n\n"
        "Твоя поддержка очень важна и мотивирует развивать бота дальше! ❤️"
    )
