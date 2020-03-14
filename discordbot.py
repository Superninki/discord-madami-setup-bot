from discord.ext import commands
import os
import sys
import traceback
import logging
import discord

bot = commands.Bot(command_prefix='/')
token = os.environ['DISCORD_BOT_TOKEN']

async def say(ctx, message):
    logging.info(message)
    await ctx.send(message)

def find_category_by_name(categories, names):
    return next(filter(lambda cate: cate.name in names, categories))

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def neko(ctx):
    await say(ctx, 'にゃーん')

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx, num_of_player_param=None, num_of_secret_voice_channel_param="3"):
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
                                        manage_messages=True, attach_files=True, read_message_history=True, speak=True)
    text_ng = discord.PermissionOverwrite(read_messages=False, send_messages=False, send_tts_messages=False,
                                       manage_messages=False, attach_files=False, read_message_history=False, speak=False)
    voice_ok = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)
    voice_ng = discord.PermissionOverwrite(view_channel=False, connect=False, speak=False)

    # カテゴリ取得
    text_category = find_category_by_name(
        guild.categories, ['テキストチャンネル', 'TEXT CHANNELS'])
    voice_category = find_category_by_name(
        guild.categories, ['ボイスチャンネル', 'VOICE CHANNELS'])

    # テキストチャンネル作成
    await text_category.create_text_channel("雑談")
    audience_channel = await text_category.create_text_channel("観戦者")

    default_permission = discord.Permissions(permissions=104324672)
    gm_permission = discord.Permissions.all()

    audience_text_channel_permission = {}
    audience_voice_channel_permission = {}
    secret_voice_channel_permission = {guild.default_role: voice_ng}
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

    logging.info(audience_text_channel_permission)
    await audience_channel.edit(overwrites=audience_text_channel_permission)

    # ボイスチャンネル作成
    for i in range(num_of_secret_voice_channel):
        await voice_category.create_voice_channel(f"密談{i+1}", overwrites=secret_voice_channel_permission)
    await voice_category.create_voice_channel("観戦者雑談", overwrites=audience_voice_channel_permission)

    await say(ctx, 'setup finished')

logging.info('start')
bot.run(token)
