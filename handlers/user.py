import asyncio
from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from states import Form
from config import GROUP_ID, SECOND_GROUP_ID, FALLBACK_INVITE_LINK
from utils.counter import get_next_id
from utils.db import find_fiscal_by_stir

router = Router()

# Telefon raqamini ulashish tugmasi
phone_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Telefon raqamni ulashish", request_contact=True)]],
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
    phone = message.contact.phone_number
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

    if not text.isdigit() or len(text) != 9:
        await message.answer("Noto‘g‘ri ma’lumot kiritdingiz. Iltimos, 9 ta raqamdan iborat STIR kiriting.")
        return

    # 1. Qidirilmoqda xabarini chiqaramiz
    search_msg = await message.answer("🔍 <b>Fiskal Modul raqami qidirilmoqda...</b>", parse_mode="HTML")
    await asyncio.sleep(0.5)

    # Bazadan qidiramiz
    found_items = find_fiscal_by_stir(text)

    # Qidirilmoqda xabarini o'chirib tashlaymiz
    try:
        await search_msg.delete()
    except Exception:
        pass

    if not found_items:
        await message.answer(
            "❌ Ushbu STIR raqami bo‘yicha bazadan ma'lumot topilmadi.\n"
            "Iltimos, STIR raqamini tekshirib qaytadan kiriting:"
        )
        return

    await state.update_data(inn=text)
    data = await state.get_data()
    phone = data.get("phone")

    # 2. Agar bitta fiskal modul topilsa
    if len(found_items) == 1:
        item = found_items[0]
        await send_to_group_and_user(message, phone, text, item["fiscal"], item["korxona"])
        await state.clear()

    # 3. Agar bir nechta fiskal modul topilsa (bir nechta kassa bo'lsa)
    else:
        buttons = []
        for item in found_items:
            btn_text = f"{item['fiscal']} ({item['manzil'][:15]}...)" if item['manzil'] else item['fiscal']
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"select_fm:{item['fiscal']}")])

        # Korxona nomini ham state ichida saqlab qo'yamiz (callback da kerak bo'ladi)
        await state.update_data(korxona=found_items[0].get("korxona", ""))

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            f"🏢 <b>{found_items[0]['korxona']}</b>\n\n"
            f"Ushbu STIR ga biriktirilgan bir nechta fiskal modul topildi. Keraklisini tanlang:",
            reply_markup=kb,
            parse_mode="HTML"
        )
        await state.set_state(Form.fiscal)


@router.callback_query(Form.fiscal, F.data.startswith("select_fm:"))
async def fiscal_selected(callback: CallbackQuery, state: FSMContext):
    fiscal = callback.data.split(":")[1]
    data = await state.get_data()
    phone = data.get("phone")
    inn = data.get("inn")
    korxona = data.get("korxona", "")

    await callback.message.delete()
    await send_to_group_and_user(callback.message, phone, inn, fiscal, korxona)
    await state.clear()
    await callback.answer()


async def send_to_group_and_user(message: Message, phone: str, inn: str, fiscal: str, korxona: str = ""):
    order_id = get_next_id()

    # 1-guruhga (ma'lumotlar bazasi guruhiga) yuboriladigan matn
    group_text = (
        f"<b>{order_id}.</b>\n\n"
        f"Telefon raqami: <code>{phone}</code>\n"
        f"INN/STIR raqami: <code>{inn}</code>\n"
        f"Fiscal Modul: <code>{fiscal}</code>"
    )
    if korxona:
        group_text += f"\nKorxona: {korxona}"

    # Ma'lumotlarni 1-guruhga yuborish
    await message.bot.send_message(chat_id=GROUP_ID, text=group_text, parse_mode="HTML")

    # 2-guruh uchun 1 martalik (faqat 1 kishi kira oladigan) havola yaratish
    try:
        invite = await message.bot.create_chat_invite_link(
            chat_id=SECOND_GROUP_ID,
            member_limit=1
        )
        invite_link = invite.invite_link
    except Exception as e:
        print(f"2-guruh uchun havola yaratishda xatolik: {e}")
        invite_link = FALLBACK_INVITE_LINK

    # Guruhga qo'shilish tugmasi
    join_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Guruhga obuna bo'lish", url=invite_link)]
    ])

    # Foydalanuvchiga yakuniy xabar va tugmani yuborish
    await message.answer(
        f"✅ <b>Ma’lumotlaringiz muvaffaqiyatli topildi va guruhga yuborildi!</b>\n\n"
        f"📞 Telefon: <code>{phone}</code>\n"
        f"📄 INN/STIR: <code>{inn}</code>\n"
        f"⚙️ <b>Fiscal Modul:</b> <code>{fiscal}</code>\n\n"
        f"Ma'lumotingiz uchun rahmat! Iltimos, kanalimizga (guruhimizga) obuna bo'ling 👇",
        reply_markup=join_keyboard,
        parse_mode="HTML"
    )