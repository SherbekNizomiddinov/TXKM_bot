from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from states import Form
from config import GROUP_ID
from utils.counter import get_next_id

router = Router()

# Telefon raqamini ulashish tugmasi
phone_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Telefon raqamni ulashish", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum!\n\n"
        "TXKM almashtrish botiga xush kelibsiz.\n"
        "Davom etish uchun telefon raqamingizni ulashing:",
        reply_markup=phone_kb
    )
    await state.set_state(Form.phone)

@router.message(Form.phone, F.contact)
async def phone_handler(message: Message, state: FSMContext):
    contact = message.contact
    phone = contact.phone_number

    # +998 formatiga keltirish
    if not phone.startswith("+"):
        phone = f"+{phone}"
    
    await state.update_data(phone=phone)
    await message.answer(
        "Rahmat!\n\nEndi <b>INN/STIR</b> raqamingizni kiriting.\n"
        "Faqat <b>9 ta raqam</b> bo‘lishi kerak.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.inn)

@router.message(Form.phone)
async def phone_wrong(message: Message):
    await message.answer(
        "Iltimos, pastdagi tugma orqali telefon raqamingizni ulashing!",
        reply_markup=phone_kb
    )

@router.message(Form.inn)
async def inn_handler(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""

    if not text.isdigit():
        await message.answer("Noto‘g‘ri ma’lumot kiritdingiz. Iltimos, faqat raqam kiriting (9 ta).")
        return

    if len(text) < 9:
        await message.answer("Iltimos, 9 ta raqamdan iborat son kiriting.")
        return

    if len(text) > 9:
        await message.answer("Noto‘g‘ri ma’lumot kiritdingiz. Iltimos, 9 ta raqam kiriting.")
        return

    await state.update_data(inn=text)
    await message.answer(
        "Yaxshi!\n\nEndi <b>Fiscal Modul</b> raqamini kiriting.\n"
        "Format: <b>2 ta katta harf + 12 ta raqam</b>\n"
        "Masalan: <code>AB123456789012</code>",
        parse_mode="HTML"
    )
    await state.set_state(Form.fiscal)

@router.message(Form.fiscal)
async def fiscal_handler(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""

    # Tekshiruv: 2 ta katta harf + 12 ta raqam
    if len(text) != 14:
        await message.answer("Noto‘g‘ri ma’lumot. Iltimos, to‘g‘ri formatda kiriting (2 katta harf + 12 raqam).")
        return

    letters = text[:2]
    digits = text[2:]

    if not letters.isalpha() or not letters.isupper():
        await message.answer("Noto‘g‘ri ma’lumot. Iltimos, to‘g‘ri ma’lumot kiriting (harflar katta bo‘lishi kerak).")
        return

    if not digits.isdigit() or len(digits) != 12:
        await message.answer("Noto‘g‘ri ma’lumot. Iltimos, to‘g‘ri ma’lumot kiriting.")
        return

    # Barcha ma’lumotlar to‘g‘ri
    data = await state.get_data()
    phone = data.get("phone")
    inn = data.get("inn")
    fiscal = text

    # Ketma-ket ID
    order_id = get_next_id()

    # Guruhga yuboriladigan xabar
    group_text = (
        f"<b>{order_id}.</b>\n\n"
        f"Telefon raqami: <code>{phone}</code>\n"
        f"INN/STIR raqami: <code>{inn}</code>\n"
        f"Fiscal Modul: <code>{fiscal}</code>"
    )

    # Guruhga yuborish
    await message.bot.send_message(
        chat_id=GROUP_ID,
        text=group_text,
        parse_mode="HTML"
    )

    await message.answer(
        "✅ Ma’lumotlaringiz muvaffaqiyatli qabul qilindi va yuborildi!\n\n"
        "Rahmat!",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()