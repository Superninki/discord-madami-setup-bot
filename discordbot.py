from discord.ext import commands
import os
import logging
import discord
import re
import random

bot = commands.Bot(command_prefix='/')
token = os.environ['DISCORD_BOT_TOKEN']


async def say(ctx, message):
    logging.info(message)
    await ctx.send(message)


# @bot.event
# async def on_command_error(ctx, error):
#     orig_error = getattr(error, "original", error)
#     error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
#     await ctx.send(error_msg)

def find_by_name(items, names):
    return next(filter(lambda item: item.name in names, items))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    result = re.match(r'^\/(\d{1,2})[dD](\d{1,3})$', message.content)
    if result:
        n = int(result[1])
        d = int(result[2])

        ds =  [random.randint(1,d) for _ in range(n)]
        total = sum(ds)
        if n == 1:
            await message.channel.send(total)
        else:
            await message.channel.send(f"{' + '.join([str(v) for v in ds])} = {total}")

    await bot.process_commands(message)


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


@bot.command()
async def pid(ctx):
    await ctx.send(os.getpid())


@bot.command()
async def neko(ctx):
    await say(ctx, 'にゃーん')


@bot.command()
@commands.has_permissions(administrator=True)
async def cleanup(ctx):
    await ctx.channel.purge(limit=1000)
    await ctx.send('I done it.')


@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx, num_of_player_param=None, num_of_secret_voice_channel_param="1"):
    if isinstance(num_of_player_param, str) and num_of_player_param.isdigit():
        num_of_player = int(num_of_player_param)
    else:
        await ctx.send("プレイヤー人数を数字で指定してください")
        return

    if num_of_secret_voice_channel_param.isdigit():
        num_of_secret_voice_channel = int(num_of_secret_voice_channel_param)
    else:
        await ctx.send("密談チャンネル数を数字で指定してください")
        return

    guild = ctx.guild

    text_ok = discord.PermissionOverwrite(read_messages=True, send_messages=True, send_tts_messages=True,
                                          manage_messages=True, attach_files=True, read_message_history=True, embed_links=True)
    text_ng = discord.PermissionOverwrite(read_messages=False, send_messages=False, send_tts_messages=False,
                                          manage_messages=False, attach_files=False, read_message_history=False)
    text_read_only = discord.PermissionOverwrite(read_messages=True, send_messages=False, send_tts_messages=False,
                                                 manage_messages=False, attach_files=False, read_message_history=True)
    voice_ok = discord.PermissionOverwrite(
        view_channel=True, connect=True, speak=True)
    voice_ng = discord.PermissionOverwrite(
        view_channel=False, connect=False, speak=False)
    voice_listen_only = discord.PermissionOverwrite(
        view_channel=True, connect=True, speak=False)

    # カテゴリ取得
    text_category = find_by_name(
        guild.categories, ['テキストチャンネル', 'TEXT CHANNELS'])
    voice_category = find_by_name(
        guild.categories, ['ボイスチャンネル', 'VOICE CHANNELS'])

    text_general = find_by_name(
        text_category.channels, ['一般', 'general']
    )
    voice_general = find_by_name(
        voice_category.channels, ['一般', 'general']
    )

    # テキストチャンネル作成
    await text_category.create_text_channel("雑談")
    audience_channel = await text_category.create_text_channel("観戦者")

    default_permission = discord.Permissions(permissions=104324672)
    gm_permission = discord.Permissions.all()

    audience_text_channel_permission = {}
    audience_voice_channel_permission = {}
    secret_voice_channel_permission = {guild.default_role: voice_listen_only}
    text_general_permission = {guild.default_role: text_read_only}
    voice_general_permission = {guild.default_role: voice_listen_only}
    # ロールと個人チャンネル作成
    await guild.create_role(name="GM", color=discord.Color.red(), permissions=gm_permission)
    for i in range(num_of_player):
        role = await guild.create_role(name=f"PL{i+1}", color=discord.Color.blue(), permissions=default_permission)
        await text_category.create_text_channel(f"{i+1}", overwrites={
            guild.default_role: text_ng,
            role: text_ok
        })
        audience_text_channel_permission[role] = text_ng
        audience_voice_channel_permission[role] = voice_ng
        secret_voice_channel_permission[role] = voice_ok
        text_general_permission[role] = text_ok
        voice_general_permission[role] = voice_ok

    logging.info(audience_text_channel_permission)
    await audience_channel.edit(overwrites=audience_text_channel_permission)
    await text_general.edit(overwrites=text_general_permission)
    await voice_general.edit(overwrites=voice_general_permission)

    # ボイスチャンネル作成
    for i in range(num_of_secret_voice_channel):
        await voice_category.create_voice_channel(f"密談{i+1}", overwrites=secret_voice_channel_permission)
    await voice_category.create_voice_channel("雑談")
    await voice_category.create_voice_channel("観戦者雑談", overwrites=audience_voice_channel_permission)

    await say(ctx, 'I done it.')

logging.info('start')
bot.run(token)
