import discord
from discord.ext import commands
from discord import app_commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import pytz

from reminder_manager import ReminderManager
import env

TOKEN = str(env.TOKEN)
CHANNEL = int(env.CHANNEL)
MESSAGE = int(env.MESSAGE)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)
scheduler = AsyncIOScheduler()
manager = ReminderManager()
jst = pytz.timezone("Asia/Tokyo")
weekday_jp = ["日", "月", "火", "水", "木", "金", "土"]

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} でログインしています")
    scheduler.start()

    to_remove = []
    for rid, r in manager.get_all().items():
        now = datetime.now(jst)
        time = r["time"]
        time_timestamp = datetime.fromisoformat(time)
        weekday = weekday_jp[int(time_timestamp.strftime("%w"))]
        time_str = time_timestamp.strftime(f"%m月%d日({weekday}) %H時%M分")
        title = r["title"]
        if time_timestamp <= now:
            to_remove.append(rid)
            continue
        if not time_timestamp + timedelta(hours = -3) <= now:
            scheduler.add_job(send_reminder, "date", run_date=time_timestamp + timedelta(hours = -3), args=[rid, 180])
        if not time_timestamp + timedelta(hours = -1) <= now:
            scheduler.add_job(send_reminder, "date", run_date=time_timestamp + timedelta(hours = -1), args=[rid, 60])
        if not time_timestamp + timedelta(minutes = -30) <= now:
            scheduler.add_job(send_reminder, "date", run_date=time_timestamp + timedelta(minutes = -30), args=[rid, 30])
        scheduler.add_job(send_passed, "date", run_date=time_timestamp, args=[rid])
    for rid in to_remove:
        manager.delete(rid)
        print(f"{time_str} 期限の提出物 {title} (ID: {rid}) は提出期限が過ぎていたため削除されました")

    scheduler.add_job(refresh_list, 'cron', hour=0)
    scheduler.add_job(refresh_list_today, 'cron', hour=7, args=[True])
    scheduler.add_job(refresh_list_tomorrow, 'cron', hour=20, args=[True])
    try:
        await refresh_list()
    except Exception as e:
        print(f"リストの更新に失敗しました: {e}")
    print("リマインダーを再設定しました")

# @bot.tree.command(name="list", description="現在追加されている提出物一覧を表示します")
# async def refresh_list(interaction: discord.Interaction):
async def refresh_list():
    channel = bot.get_channel(CHANNEL)
    list_message = await channel.fetch_message(MESSAGE)
    reminders = [
        (reminder_id, r) for reminder_id, r in manager.reminders.items()
    ]
    sorted_reminders = sorted(reminders, key=lambda item: datetime.fromisoformat(item[1]['time']))

    if not reminders:
        # await interaction.response.send_message("提出物はありません", ephemeral=True)
        await list_message.edit(content="提出物はありません")
        return

    lines = ["## 提出物"]
    for reminder_id, r in sorted_reminders:
        time = r["time"]
        time_timestamp = datetime.fromisoformat(time)
        weekday = weekday_jp[int(time_timestamp.strftime("%w"))]
        time_str = time_timestamp.strftime(f"%m月%d日({weekday}) %H時%M分")
        title = r["title"]
        lines.append(f" - **{time_str}**  **{title}** (ID: `{reminder_id}`)")

    list = "\n".join(lines)
    today = await refresh_list_today(False)
    tomorrow = await refresh_list_tomorrow(False)
    print = list + "\n\n" + today + "\n\n" + tomorrow
    await list_message.edit(content=print)
    # await interaction.response.send_message("\n".join(lines), ephemeral=True)

async def refresh_list_today(send):
    channel = bot.get_channel(CHANNEL)
    today = date.today()
    reminders = [
        (reminder_id, r) for reminder_id, r in manager.reminders.items()
    ]
    reminders_today = []

    # if not reminders:
    #     if send:
    #         await channel.send("@everyone\n今日が提出期限の提出物はありません")
    #     else:
    #         await list_message.edit(content="今日が提出期限の提出物はありません")
    #     return

    for reminder_id, r in reminders:
        time = r["time"]
        time_timestamp = datetime.fromisoformat(time)
        if time_timestamp.date() == today:
            reminders_today.append((reminder_id, r))

    if not reminders_today:
        if send:
            await channel.send("今日が提出期限の提出物はありません")
        return "今日が提出期限の提出物はありません"

    sorted_reminders_today = sorted(reminders_today, key=lambda item: datetime.fromisoformat(item[1]['time']))

    lines = ["## 今日が提出期限の提出物"]
    for reminder_id, r, in sorted_reminders_today:
        time = r["time"]
        time_timestamp = datetime.fromisoformat(time)
        time_str = time_timestamp.strftime("%H時%M分")
        title = r["title"]
        lines.append(f" - **{time_str}**  **{title}** (ID: `{reminder_id}`)")
    if send:
        await channel.send("@everyone\n" + "\n".join(lines))
    return "\n".join(lines)
    # await interaction.response.send_message("\n".join(lines), ephemeral=True)

async def refresh_list_tomorrow(send):
    channel = bot.get_channel(CHANNEL)
    tomorrow = date.today() + timedelta(days = 1)
    reminders = [
        (reminder_id, r) for reminder_id, r in manager.reminders.items()
    ]
    reminders_tomorrow = []

    # if not reminders:
    #     if send:
    #         await channel.send("@everyone\n今日が提出期限の提出物はありません")
    #     else:
    #         await list_message.edit(content="今日が提出期限の提出物はありません")
    #     return

    for reminder_id, r in reminders:
        time = r["time"]
        time_timestamp = datetime.fromisoformat(time)
        if time_timestamp.date() == tomorrow:
            reminders_tomorrow.append((reminder_id, r))

    if not reminders_tomorrow:
        if send:
            await channel.send("明日が提出期限の提出物はありません")
        return "明日が提出期限の提出物はありません"

    sorted_reminders_tomorrow = sorted(reminders_tomorrow, key=lambda item: datetime.fromisoformat(item[1]['time']))

    lines = ["## 明日が提出期限の提出物"]
    for reminder_id, r, in sorted_reminders_tomorrow:
        time = r["time"]
        time_timestamp = datetime.fromisoformat(time)
        time_str = time_timestamp.strftime("%H時%M分")
        title = r["title"]
        lines.append(f" - **{time_str}**  **{title}** (ID: `{reminder_id}`)")
    if send:
        await channel.send("@everyone\n" + "\n".join(lines))
    return "\n".join(lines)
    # await interaction.response.send_message("\n".join(lines), ephemeral=True)

async def send_passed(reminder_id):
    # reminder = manager.reminders.get_id(reminder_id)
    reminder = manager.get_id(reminder_id)
    if not reminder:
        return
    channel = bot.get_channel(CHANNEL)
    title = reminder["title"]
    if channel:
        await channel.send(f"@everyone\n**{title}** の提出期限です")
    manager.delete(reminder_id)
    await refresh_list()

async def send_reminder(reminder_id, time):
    # reminder = manager.reminders.get_id(reminder_id)
    reminder = manager.get_id(reminder_id)
    if not reminder:
        return
    hours = int(time / 60)
    minutes = time % 60
    if hours == 0:
        time_str = f"{minutes}分"
    elif minutes == 0:
        time_str = f"{hours}時間"
    else:
        time_str = f"{hours}時間 {minutes}分"
    channel = bot.get_channel(CHANNEL)
    title = reminder["title"]

    if channel:
        await channel.send(f"@everyone\n**{title}** の提出期限まであと **{time_str}** です")

@bot.tree.command(name="add", description="提出物を追加します")
@app_commands.describe(
    month="月 (1-12)",
    day="日 (1-31)",
    hour="時 (0-23)",
    minute="分 (0-59)",
    title="タイトル"
)
async def add(interaction: discord.Interaction, month: int, day: int, hour: int, minute: int, title: str):
    if not int(interaction.channel.id) == CHANNEL:
        await interaction.response.send_message("このチャンネルでは使用できません\n専用チャンネルで使うことができます", ephemeral=True)
        return
    await interaction.response.defer(thinking=True, ephemeral=True)
    now = datetime.now(jst)
    channel = bot.get_channel(CHANNEL)
    try:
        target_time = jst.localize(datetime(now.year, month, day, hour, minute))
    except ValueError:
        await interaction.followup.send("日時が無効です")
        return

    if target_time <= now:
        target_time = target_time + relativedelta(year = now.year + 1)
    weekday = weekday_jp[int(target_time.strftime("%w"))]
    time_str = target_time.strftime(f"%m月%d日({weekday}) %H時%M分")

    reminder_id = manager.add(
        time=target_time.isoformat(),
        title=title
    )

    if not target_time + timedelta(hours = -3) <= now:
        scheduler.add_job(send_reminder, "date", run_date=target_time + timedelta(hours = -3), args=[reminder_id, 180])
    if not target_time + timedelta(hours = -1) <= now:
        scheduler.add_job(send_reminder, "date", run_date=target_time + timedelta(hours = -1), args=[reminder_id, 60])
    if not target_time + timedelta(minutes = -30) <= now:
        scheduler.add_job(send_reminder, "date", run_date=target_time + timedelta(minutes = -30), args=[reminder_id, 30])
    scheduler.add_job(send_passed, "date", run_date=target_time, args=[reminder_id])

    try:
        await refresh_list()
    except Exception as e:
        print(f"リストの更新に失敗しました: {e}")
        await channel.send(f"リストの更新に失敗しました: {e}")
    await interaction.followup.send("正常に登録されました")
    await channel.send(f"<@{interaction.user.id}> によって **{time_str}** 提出期限の提出物 **{title}** (ID: `{reminder_id}`) が登録されました")

# 通知削除用のView
class ConfirmView(discord.ui.View):
    def __init__(
        self,
        reminder_id,
        user_id,
        title,
        time_str
    ):
        super().__init__(timeout=30)
        self.reminder_id = reminder_id
        self.value = None
        self.user_id = user_id
        self.title = title
        self.time_str = time_str

    @discord.ui.button(label="削除", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        # self.reminder = manager.reminders.get_id(self.reminder_id)
        # self.time = self.reminder["time"]
        # self.title = self.reminder["title"]
        self.channel = bot.get_channel(CHANNEL)
        # self.user = interaction.uesr.id

        manager.delete(self.reminder_id)
        try:
            await refresh_list()
        except Exception as e:
            print(f"リストの更新に失敗しました: {e}")
            await self.channel.send(f"リストの更新に失敗しました: {e}")
        # await interaction.response.edit_message(content=f"@everyone\n**{self.time}** 期限の提出物 **{self.title}** (ID: `{self.reminder_id}`) を削除しました。", view=None, ephemeral=False)
        await interaction.response.edit_message(content="正常に削除されました", view=None)
        await self.channel.send(content=f"<@{self.user_id}> によって **{self.time_str}** 提出期限の提出物 **{self.title}** (ID: `{self.reminder_id}`) が削除されました")
        self.stop()

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="削除をキャンセルしました", view=None)
        self.value = False
        self.stop()

@bot.tree.command(name="delete", description="IDを指定して提出物を削除します")
@app_commands.describe(reminder_id="削除する提出物のID")
async def delete(interaction: discord.Interaction, reminder_id: str):
    if not int(interaction.channel.id) == CHANNEL:
        await interaction.response.send_message("このチャンネルでは使用できません\n専用チャンネルで使うことができます", ephemeral=True)
        return
    if reminder_id not in manager.reminders:
        await interaction.response.send_message("指定されたIDの提出物は存在しません", ephemeral=True)
        return

    reminder = manager.get_id(reminder_id)
    title = reminder["title"]
    time = reminder["time"]
    time_timestamp = datetime.fromisoformat(time)
    weekday = weekday_jp[int(time_timestamp.strftime("%w"))]
    time_str = time_timestamp.strftime(f"%m月%d日({weekday}) %H時%M分")

    view = ConfirmView(
        reminder_id,
        interaction.user.id,
        title,
        time_str
    )
    await interaction.response.send_message(f"**{time_str}** 提出期限の提出物 **{title}** (ID: `{reminder_id}`) を本当に削除しますか？", view=view, ephemeral=True)

bot.run(TOKEN)

