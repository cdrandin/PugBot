import json

import battlenet
import requests
from battlenet import Character, Connection

LEG_WITH_SOCKET = [
    132369, 132410, 137044, 132444, 132449, 132452, 132460, 133973, 133974, 137037, 137038, 137039, 137040,
    137041, 137042, 137043, 132378, 137045, 137046, 137047, 137048, 137049, 137050, 137051, 137052, 137054, 137055,
    137220, 137223, 137276, 137382, 138854
]

ENCHANTABLE_SLOTS = ["neck", "back", "finger1", "finger2"]
GEMMABLE_SLOTS = ["back", "chest", "feet", "finger1", "finger2", "hands",
                  "head", "legs", "main_hand", "neck", "off_hand", "ranged",
                  "shoulder", "trinket1", "trinket2", "waist", "wrist"]

config = json.loads(open("config.json").read())  # Load Configs
API_KEY = config["blizzard_api_key"]
default_region = config["default_region"]

Connection.setup(
    api_key=API_KEY,
    locale=default_region)


def get_sockets(equipment):
    """
    Return dict with total sockets and count of equipped gems and slots that are missing

    :param player_dictionary: Retrieved player dict from API
    :return: dict()
    """
    current_sockets = available_sockets = 0

    for slot in GEMMABLE_SLOTS:
        item = getattr(equipment, slot)
        if item:
            if slot in ["main_hand", "off_hand"]:
                continue

            current_sockets += len(item.gems)
            available_sockets += 1 if 1808 in item._data["bonusLists"] else 0

    return {"total_sockets": available_sockets,
            "equipped_gems": current_sockets}


def get_enchants(equipment):
    """
    Get count of enchants missing and slots that are missing
    :param player_dictionary:
    :return: dict()
    """
    missing_enchant_slots = []
    for slot in ENCHANTABLE_SLOTS:
        item = getattr(equipment, slot)
        if item.enchant is None:
            missing_enchant_slots.append(slot)

    return {
        "enchantable_slots": len(ENCHANTABLE_SLOTS),
        "missing_slots": missing_enchant_slots,
        "total_missing": len(missing_enchant_slots)
    }


def get_raid_progression(progression, raid_name):
    raid = next(raid for raid in progression[
                "raids"] if raid.name == raid_name)

    normal = 0
    heroic = 0
    mythic = 0

    for boss in raid._data["bosses"]:
        if boss["normalKills"] > 0:
            normal += 1
        if boss["heroicKills"] > 0:
            heroic += 1
        if boss["mythicKills"] > 0:
            mythic += 1

    return {"normal": normal,
            "heroic": heroic,
            "mythic": mythic,
            "total_bosses": len(raid._data["bosses"])}


def get_mythic_progression(character):
    achievements = character._data["achievements"]
    plus_two = 0
    plus_five = 0
    plus_ten = 0

    if 33096 in achievements["criteria"]:
        index = achievements["criteria"].index(33096)
        plus_two = achievements["criteriaQuantity"][index]

    if 33097 in achievements["criteria"]:
        index = achievements["criteria"].index(33097)
        plus_five = achievements["criteriaQuantity"][index]

    if 33098 in achievements["criteria"]:
        index = achievements["criteria"].index(33098)
        plus_ten = achievements["criteriaQuantity"][index]

    return {
        "plus_two": plus_two,
        "plus_five": plus_five,
        "plus_ten": plus_ten
    }


def get_char(name, server):
    return_string = ""
    try:
        character = Character(battlenet.UNITED_STATES, server, name, fields=[
            Character.GUILD, Character.ITEMS, Character.PROGRESSION,
            Character.ACHIEVEMENTS])
    except Exception as e:
        raise e

    return_string += "**%s** - **%s** - **%s %s**\n" % (
        character.name, character.get_realm_name(), character.level, character.get_class_name())

    return_string += "Last Modified: {}\n".format(
        character.last_modified.strftime("%x - %I:%M:%S %p"))

    armory_url = "http://us.battle.net/wow/en/character/{}/{}/advanced".format(
        character.get_realm_name(), character.name)

    # Raid Progression
    en_progress = get_raid_progression(
        character.progression, "The Emerald Nightmare")

    tov_progress = get_raid_progression(
        character.progression, "Trial of Valor")

    mythic_progress = get_mythic_progression(character)

    sockets = get_sockets(character.equipment)
    enchants = get_enchants(character.equipment)

    return_string += "<{}>\n".format(armory_url)

    return_string += "```CSS\n"  # start Markdown

    # iLvL
    return_string += "Equipped Item Level: %s\n" % character.equipment.average_item_level_equipped

    # Mythic Progression
    return_string += "Mythics: +2: %s, +5: %s, +10: %s\n" % (mythic_progress["plus_two"],
                                                             mythic_progress[
                                                                 "plus_five"],
                                                             mythic_progress["plus_ten"])

    return_string += "EN: {1}/{0} (N), {2}/{0} (H), {3}/{0} (M)\n".format(en_progress["total_bosses"],
                                                                          en_progress[
                                                                              "normal"],
                                                                          en_progress[
                                                                              "heroic"],
                                                                          en_progress["mythic"])

    return_string += "TOV: {1}/{0} (N), {2}/{0} (H), {3}/{0} (M)\n".format(tov_progress["total_bosses"],
                                                                           tov_progress[
                                                                               "normal"],
                                                                           tov_progress[
                                                                               "heroic"],
                                                                           tov_progress["mythic"])

    # Gems
    return_string += "Gems Equipped: %s/%s\n" % (
        sockets["equipped_gems"], sockets["total_sockets"])

    # Enchants
    return_string += "Enchants: %s/%s\n" % (enchants["enchantable_slots"] - enchants["total_missing"],
                                            enchants["enchantable_slots"])
    if enchants["total_missing"] > 0:
        return_string += "Missing Enchants: {0}".format(
            ", ".join(enchants["missing_slots"]))

    return_string += "```"  # end Markdown

    return return_string


async def pug(client, message):
    try:
        i = str(message.content).split(" ")
        name = i[1]
        server = i[2]
        character_info = get_char(name, server)
        await client.send_message(message.channel, character_info)
    except Exception as e:
        print(e)
        await client.send_message(message.channel, "Error With Name or Server\n"
                                                   "Use: !pug <name> <server>\n"
                                                   "Hyphenate Two Word Servers (Ex: Twisting-Nether)")


def main():
    info = get_char("monkinthebox", "Lightbringer")
    print(info)

if __name__ == "__main__":
    main()
