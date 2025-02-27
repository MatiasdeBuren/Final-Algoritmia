from pyswip import Prolog
from random import randint

prolog = Prolog()
prolog.consult("spell_logic.pl") #consulto el archivo de prolog
prolog.retract("warrior(you, Health)")
#resetear vida de los jugadores
prolog.retract("warrior(boss, Health)")
prolog.retractall("mana(you, _)")
prolog.assertz("mana(you, 100)")
prolog.assertz("max_turns(8)")
prolog.assertz("warrior(you, 200)")
prolog.assertz("warrior(boss, 200)")
#prolog.assertz("mana(you, 100)")
#inicializar cooldowns
list(prolog.query("initialize_cooldowns."))
list(prolog.query("initialize_cooldowns_berserk."))

trap_dictionary = {"you": [], "boss": []} #diccionario de trampas, se guardan en el formato {victima: letra}
disable_dictionary = {"you": [], "boss": []} #diccionario letras desactivadas, se guardan en el formato {victima: letra}
mostCommonLetters = {chr(i): 0 for i in range(97, 123)}  # Diccionario para contar letras a-z

def update_letter_count(string):
    for char in string.lower():
        if char in mostCommonLetters:
            mostCommonLetters[char] += 1

def format_to_print(string):
    return " ".join(string.split("_")).upper()

def format_to_prolog(string):
    return string.replace(" ", "_").lower()

def first_turn():
    print("Welcome to the game!")
    print("You're a word wizard!")
    print("Any spells you type will be casted! Pretty neat huh?")
    print("Why don't you give it a try?\n")
    user_turn()
    print("Seems someone's mad, whoops!")
    print("Oh well! My job here is done!")
    print("Good luck man!\n")

def end_game():
    print("-------------------------------------------------------------------")
    print("GAME OVER")
    you_hp = list(prolog.query("warrior(you, Health)"))[0]["Health"]
    boss_hp = list(prolog.query("warrior(boss, Health)"))[0]["Health"]
    if you_hp <= 0 and boss_hp <= 0:
        print("What even was your plan dude?")
    elif you_hp <= 0:
        print("YOU LOST!")
    else:
        print("YOU WON!")

def load_spell_lists(user, visible_spells, secret_spells, traps):
    for spell in prolog.query(f"secret({user}, Spell)"):
        secret_spells.append(format_to_print(spell["Spell"]))
    spells = list(prolog.query("spell(Name)"))
    for spell in spells:
        spell_name = format_to_print(spell["Name"])
        if spell_name in secret_spells:
            continue
        visible_spells.append(spell_name)
    for trap in prolog.query("trap(Name)"):
        traps.append(format_to_print(trap["Name"]))

def load_cooldowns(user, cooldowns):
    spells = list(prolog.query("spell(Name)")) + list(prolog.query("spell_berserk(Name)"))
    print(list(prolog.query(f"current_cooldown(boss, berserk_fireball, CD)")))
    for spell in spells:
        spell_data = spell["Name"]
        cooldown = list(prolog.query(f"current_cooldown({user}, {spell_data}, CD)"))[0]["CD"]
        cooldowns[spell_data] = cooldown

def update_cooldown(user, spell_data):
    list(prolog.query(f"update_single_cooldown({user}, {spell_data})."))

def can_cast_spell(user, spell_data):
    if user == "you":
        return list(prolog.query(f"can_cast_spell({user}, {spell_data})")) and list(prolog.query(f"has_mana({user}, {spell_data})"))
    else:
        return list(prolog.query(f"can_cast_spell({user}, {spell_data})"))

def choose_letter():
    sorted_letters = sorted(mostCommonLetters.items(), key=lambda item: item[1], reverse=True)
    for letter, _ in sorted_letters:
        if letter not in trap_dictionary["you"] and letter not in disable_dictionary["you"]:
            return letter

def is_valid_spell(spell_data, caster):
    for letter in disable_dictionary[caster]:
        if letter in spell_data:
            return False
    return can_cast_spell(caster, spell_data)

def handle_trap(spell_data, caster, target):
    if caster == "you":
        letter = input_trap_letter(target)
    else:
        letter = choose_letter()
    
    if spell_data == "trap_key" and len(trap_dictionary[target]) < 2:
        cast_trap(spell_data, caster, letter)
        trap_dictionary[target].append(letter)
        return True
    elif spell_data == "disable_key" and len(disable_dictionary[target]) == 0:
        cast_trap(spell_data, caster, letter)
        disable_dictionary[target].append(letter)
        return True
    return False

def update_max_turns():
    max_turns = list(prolog.query("max_turns(Max)"))[0]["Max"]
    prolog.retractall("max_turns(_)")
    prolog.assertz(f"max_turns({max_turns - 1})")
    print("Actualizando turnos restantes...")
    updated_turns = list(prolog.query("max_turns(Max)"))[0]["Max"]
    print(f"Turnos restantes: {updated_turns}")

def update_mana(caster, spell_data):
    if caster == "you":
        mana = list(prolog.query("mana(you, Mana)"))[0]["Mana"]
        mana_cost = list(prolog.query(f"mana_cost({spell_data}, Cost)"))[0]["Cost"]
        prolog.retract("mana(you, _)")
        prolog.assertz(f"mana(you, {mana - mana_cost})")

def is_counter_spell_on(spell_data, caster):
    opponent = "boss" if caster == "you" else "you"

    # Si el enemigo tiene activo un counter_spell, lo detiene y le hace daño
    counter_check = list(prolog.query(f"secret({opponent}, counter_spell)"))
    if counter_check:
        list(prolog.query(f"counter_spell({opponent}, {caster})"))
        print(f"{opponent} bloqueó el hechizo con un Counter Spell y {caster} recibió daño!")
        return True  # El hechizo del caster no se ejecuta
    return False

def handle_cast(spell_data, caster):
    if not is_valid_spell(spell_data, caster):
        if caster == "you":
            if list(prolog.query(f"has_mana({caster}, {spell_data})")):
                print(f"{format_to_print(spell_data)} is on cooldown or contains a disabled letter!")
            else:
                print(f"You don't have enough mana to cast {format_to_print(spell_data)}!")
        return False
    check_trap(spell_data, caster)
    if list(prolog.query(f"warrior({caster}, Health)"))[0]["Health"] <= 0:
        return False
    if is_counter_spell_on(spell_data, caster):
        print (f"{format_to_print(spell_data)} was countered!")
        return False
    cast_spell(spell_data, caster)
    if caster == "you":
        update_letter_count(spell_data)
    update_cooldown(caster, spell_data)
    update_mana(caster, spell_data)
    return True

def user_turn():
    print("----YOUR TURN-------------------------------------------------------------------")
    visible_spells = []
    secret_spells = []
    traps = []
    cooldowns = {}
    load_spell_lists("you", visible_spells, secret_spells, traps)
    load_cooldowns("you", cooldowns)
    valid = False
    while not valid:
        print("\nKnown spells:", [f"{spell} (CD: {cooldowns[format_to_prolog(spell)]})" for spell in visible_spells])
        print("Traps:", traps)
        print("Type HELP to check a spell's description or SKIP to skip your turn.\n")
        print('Current Mana:', list(prolog.query("mana(you, Mana)"))[0]["Mana"])
        spell = input().upper()
        spell_data = format_to_prolog(spell)
        if spell == "HELP":
            help_handler(visible_spells, secret_spells, traps)
        elif spell == "SKIP":
            #refills mana
            max_mana = list(prolog.query("max_mana(you, X)"))[0]["X"]
            prolog.retract("mana(you, _)")
            prolog.assertz(f"mana(you, {max_mana})")
            print("Skipping turn...\n")
            valid = True
        elif spell in traps:
            valid = handle_trap(spell_data, "you", "boss")
        elif spell in visible_spells or spell in secret_spells:
            if spell in secret_spells:
                print("Hey that's a secret!")
                prolog.retract(f"secret(you, {spell_data})")
            valid = handle_cast(spell_data, "you")
        else:
            print("Invalid spell, try again!\n")
    return

def input_trap_letter(target):
    while True:
        letter = input("\nType a letter to cast the trap: ").lower()
        if len(letter) != 1:
            print("Please type a single letter!")
            continue
        if any(f[1] == letter for f in trap_dictionary[target]):
            print(f"The letter {letter} is already trapped!")
            continue
        break
    return letter

def help_handler(visible_spells,secret_spells,traps):
    print("\nHELP-------------------------------------------------------------------")
    print("Select a spell or trap to see its description")
    valid = False
    while(valid == False):
        print("Known spells:", visible_spells)
        print("Known traps:", traps)
        print("Type BACK when you're ready to cast a spell.\n")
        spell = input().upper()
        spell_data = format_to_prolog(spell)
        if spell in visible_spells or spell in traps:  # si el spell es conocido
            print_data(spell_data)
        elif spell in secret_spells:  # si el spell es un spell especial
            print("Hey that's a secret!")
            prolog.retract(f"secret(you, {spell_data})")
            visible_spells.append(spell)
            secret_spells.remove(spell)
            print_data(spell_data)
        elif spell == "BACK":
            valid = True
        else:
            print("That's not a spell silly!")

def print_data(spell_data):
    print("-------------------------------------------------------------------")
    print(format_to_print(spell_data), "-", list(prolog.query(f"description({spell_data}, Desc)"))[0]["Desc"])
    damage = list(prolog.query(f"damage_range({spell_data}, Min, Max)"))
    match spell_data:
        case "heal":
            print(f"Heals {damage[0]['Min']} to {damage[0]['Max']} hp")
        case "trap_key":
            print(f"Deals {damage[0]['Min']} damage for every instance of the letter in a spell.")
        case "disable_key":
            print("You can only cast this once.")
        case _:
            print(f"Deals {damage[0]['Min']} to {damage[0]['Max']} damage")
    print("-------------------------------------------------------------------\n")

def cast_spell(spell_data,caster):
    #lógica para castear un spell
    #CHECK SI HAY LETRAS TRAPPEADAS
    # check el target del spell, puede ser un solo target o una lista de targets
    target_list = [target["Target"] for target in prolog.query(f"target({spell_data}, {caster}, Target)")]
    print(f"\n{format_to_print(caster)} casted {format_to_print(spell_data)}")
    # check si es crítico
    if spell_data == "counter_spell":
        prolog.assertz(f"secret({caster}, counter_spell)")
        print(f"{caster} lanzó Counter Spell! Si el enemigo lanza un hechizo, será bloqueado y recibirá daño.")
        return True

    crit_modifier = 1
    crit_chance = list(prolog.query(f"crit_chance({spell_data}, Chance)"))[0]["Chance"]
    if randint(0, 100) < crit_chance:
        print("Critical hit!")
        if spell_data == "summon_frog": #easter egg, si el usuario hace un critico con SUMMON FROG, se invoca un dragon
            print("That's a big frog!")
            cast_spell("summon_dragon", caster)
            return
        else:
            crit_modifier = 2
    #calculo daño
    damage_range = list(prolog.query(f"damage_range({spell_data}, Min, Max)"))[0]
    damage = randint(damage_range["Min"], damage_range["Max"]) * crit_modifier 
    #handle daño a los objetivos
    for target in target_list:
        #query vida actual
        current_health = list(prolog.query(f"warrior({target}, Health)"))[0]["Health"]
        #actualizo vida del objetivo e imprimo
        prolog.retract(f"warrior({target}, {current_health})")
        if spell_data == "heal":
            prolog.assertz(f"warrior({target}, {current_health + damage})")
            print(f"{format_to_print(target)} healed {damage} hp!")
        else:
            prolog.assertz(f"warrior({target}, {current_health - damage})")
            print(f"Dealt {damage} damage to {format_to_print(target)}")
        #imprimo resultado

        if list(prolog.query(f"warrior({target}, Health)"))[0]["Health"] < 0:
            print(f"O V E R K I L L")
    prolog.query(f"update_single_cooldown({caster}, {spell_data})")

def cast_trap(trap_data, caster, letter):
    target = list(prolog.query(f"target({trap_data}, {caster}, Target)"))[0]["Target"]
    print(f"{format_to_print(caster)} casted {format_to_print(trap_data)} on letter {letter.upper()}\n")


def check_trap(spell_data, caster):
    #check si el spell tiene una letra trappeada
    for trap in trap_dictionary[caster]:
        if trap in spell_data: #si el spell tiene una letra trappeada
            damage = list(prolog.query(f"damage_range(trap_key, Min, Max)"))[0]["Min"] * spell_data.count(trap)
            #query vida actual
            current_health = list(prolog.query(f"warrior({caster}, Health)"))[0]["Health"]
            #actualizo vida del objetivo e imprimo
            prolog.retract(f"warrior({caster}, {current_health})")
            prolog.assertz(f"warrior({caster}, {current_health - damage})")
            print(f"The letter {format_to_print(trap)} was trapped!")
            print(f"Dealt {damage} damage to {format_to_print(caster)}")
            print(f"{format_to_print(caster)} health: {list(prolog.query(f'warrior({caster}, Health)'))[0]['Health']}\n")
            trap_dictionary[caster].remove(trap)
            if list(prolog.query(f"warrior({caster}, Health)"))[0]["Health"] <= 0:
                print(f"Did {caster} just die to a trap?\n")

def behead(caster,target):
    berserk_mode = int(bool(list(prolog.query("berserker_mode(boss)"))))
    if caster == "boss" and berserk_mode:
        spells = list(prolog.query("spell_berserk(Name)"))
    else:
        spells = list(prolog.query("spell(Name)"))
        #remove one shots and heal
        spells.remove({"Name": "summon_dragon"})
        spells.remove({"Name": "heal"})
        spells.remove({"Name": "nuke"})

    for spell in spells:
        spell_data = spell["Name"]
        if is_valid_spell(spell_data, caster):
            if list(prolog.query(f"damage_range({spell_data}, Min, Max)"))[0]["Min"] >= list(prolog.query(f"warrior({target}, Health)"))[0]["Health"]:
                return True
    return False

def boss_turn(show_boss_logic):
    print("----BOSS TURN-------------------------------------------------------------------")
    #is boss one hp?
    is_1_hp = int(bool(list(prolog.query("is_one_hp(boss)"))))
    #can boss die to any spells next turn?
    can_die = int(bool(behead("you", "boss")))
    #does the boss have 2 active traps?
    at_trap_limit = int(len(trap_dictionary["you"]) == 2)
    #has the boss disabled a letter already?
    has_disabled = int(len(disable_dictionary["you"]) == 1)
    #can the boss kill warrior in one turn?
    can_kill = int(bool(behead("boss", "you")))
    #berserker mode implies no cooldowns and double damage
    berserker_mode = int(bool(list(prolog.query("berserker_mode(boss)"))))
    #boss can end fight based on max turns
    max_remaining_turns = list(prolog.query("max_turns(Max)"))[0]["Max"]
    max_turns_passed = int(max_remaining_turns <= 0)

    possible_actions = list(prolog.query(f"boss_choice(Action,{is_1_hp}, {can_die}, {at_trap_limit}, {has_disabled}, {can_kill}, {berserker_mode}, {max_turns_passed})"))
    cooldowns = list(prolog.query("current_cooldown(boss, Spell, CD)"))
    #print("cooldowns:", cooldowns)
    if show_boss_logic:
        print(f"Boss is at 1 hp: {is_1_hp}")
        print(f"Boss can die next turn: {can_die}")
        print(f"Boss is at trap limit: {at_trap_limit}")
        print(f"Boss has disabled a letter: {has_disabled}")
        print(f"Boss can kill warrior: {can_kill}")
        print(f"Boss is in berserker mode: {berserker_mode}")
        print(f"Boss can end fight based on max turns: {max_turns_passed}")
        print("BOSS' CHOICE")
    
    spell_data = None
    for action in possible_actions:
        if action['Action'] == "trap_key" or action['Action'] == "disable_key":
            spell_data = action['Action']
            break
        elif is_valid_spell(action['Action'], "boss"):
            spell_data = action['Action']
            break
    
    if spell_data is None:
        print("Boss gave up....\n")
        return
    print(f"Boss chose {format_to_print(spell_data)}\n")
    if not handle_trap(spell_data, "boss", "you"):
        handle_cast(spell_data, "boss")
    return

def main():
    warriors = list(prolog.query(f"warrior(Warrior, Health)"))

    show_boss_logic = False
    if input("Show boss' logic? (Yes/No): ").lower() == 'yes':
        show_boss_logic = True

    first_turn()
    update_max_turns()
    warriors = list(prolog.query(f"warrior(Warrior, Health)")) #actualizo vida de los jugadores
    while warriors[0]["Health"] > 0 and warriors[1]["Health"] > 0:
        boss_turn(show_boss_logic)
        update_max_turns()
        warriors = sorted(
            list(prolog.query(f"warrior(Warrior, Health)")),
            key=lambda x: x["Warrior"]  # Ensure consistent order
        )
        prolog.retractall("secret(counter_spell)")

        print("-------------------------------------------------------------------")
        print("Current health:")
        print("You:", warriors[1]["Health"])
        print("Boss:", warriors[0]["Health"])
        print("-------------------------------------------------------------------")
        print("Trapped keys:", trap_dictionary)
        print("Disabled keys:", disable_dictionary)
        print("Passed turns:", 8 - list(prolog.query("max_turns(Max)"))[0]["Max"])
        print("\n")


        list(prolog.query("update_cooldowns."))
        if warriors[0]["Health"] > 0 and warriors[1]["Health"] > 0:
            user_turn()
            update_max_turns()
            #retracts all counterSpelss after the user's turn
            
            warriors = list(prolog.query(f"warrior(Warrior, Health)"))
    end_game()
main()