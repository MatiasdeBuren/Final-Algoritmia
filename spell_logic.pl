:- dynamic warrior/2.
:- dynamic mana/2.
:- dynamic opponent/2.
:- dynamic spell/1.
:- dynamic description/2.
:- dynamic damage_range/3.
:- dynamic crit_chance/2.
:- dynamic can_cast/2.
:- dynamic secret/2.
:- dynamic can_cast_trap/3. 
:- dynamic current_cooldown/3.
:- dynamic initialize_cooldowns/0.
:- dynamic initialize_cooldowns_berserk/0.
:- dynamic update_cooldowns/0.
:- dynamic can_cast_spell/2.


max_health(you,200).
max_health(boss,200).
max_mana(you,100).
mana(you, max_mana(you)).
warrior(you,max_health(you)).
warrior(boss,max_health(boss)).
opponent(you,boss).
opponent(boss,you).




% Se activa si el enemigo lanza un hechizo
secret_spell(counter_spell).

secret_spell_on(you,counter_spell).

spell(fireball).
spell(ice).
spell(lightning).
spell(counter_spell).
spell(summon_frog).
spell(summon_dragon).
spell(counter_spell).
spell(nuke).
spell(heal).


spell_berserk(berserk_fireball).
spell_berserk(berserk_ice).
spell_berserk(berserk_lightning).
spell_berserk(berserk_summon_frog).

trap(trap_key).
trap(disable_key).

description(fireball, 'Shoot a fireball at your enemy.').
description(ice, 'Shoot an ice shard at your enemy.').
description(lightning, 'Shoot lightning at your enemy.').
description(summon_frog, 'Summon a frog, ribbit!').
description(summon_dragon, 'Thats not a frog!').
description(nuke, 'Uh oh! You shouldnt use this.').
description(heal, 'Heal yourself a little bit.').
description(trap_key, 'Lays a trap on one of your opponents keys.\nOnly two traps can be active at once.').
description(disable_key, 'Disables one of your opponents keys!.\nOnly one key can be disabled at once.').

damage_range(fireball, 20, 50).
damage_range(ice, 15, 40).
damage_range(lightning, 25, 60).
damage_range(counter_spell, 10, 30).
damage_range(summon_frog, 5, 15).
damage_range(summon_dragon, 145, 145).
damage_range(nuke, 5000, 10000).
damage_range(heal, 10, 15).
damage_range(trap_key, 15,15).
damage_range(disable_key, 0, 0).
damage_range(berserk_fireball, 40, 100).
damage_range(berserk_ice, 30, 80).
damage_range(berserk_lightning, 50, 120).
damage_range(berserk_summon_frog, 10, 30).


crit_chance(fireball, 20).
crit_chance(ice, 10).
crit_chance(lightning, 30).
crit_chance(counter_spell, 20).
crit_chance(summon_frog, 10).
crit_chance(summon_dragon, 0).
crit_chance(nuke, 100).
crit_chance(heal, 15).
crit_chance(berserk_fireball, 20).
crit_chance(berserk_ice, 10).
crit_chance(berserk_lightning, 30).
crit_chance(berserk_summon_frog, 10).
crit_chance(berserk_summon_dragon, 0).

mana_cost(fireball, 20).
mana_cost(ice, 10).
mana_cost(lightning, 30).
mana_cost(counter_spell, 10).
mana_cost(summon_frog, 10).
mana_cost(summon_dragon, 90).
mana_cost(heal, 20).

target(Spell, Caster, Opponent) :- 
    (spell(Spell) ; spell_berserk(Spell)), 
    Spell \= heal, 
    warrior(Caster, _), 
    opponent(Caster, Opponent).

target(nuke,Caster,Caster) :- opponent(Caster,_), warrior(Caster,_).
target(heal,Caster,Caster) :- warrior(Caster,_),warrior(Caster,_).
target(Trap,Caster,Opponent) :- trap(Trap), warrior(Caster,_), opponent(Caster,Opponent).

secret(you,nuke).
secret(you,summon_dragon).
secret(boss,nuke).
secret(boss,summon_dragon).

is_one_hp(Warrior) :- warrior(Warrior,1).

can_die(Warrior) :-
    warrior(Warrior, HP),
    damage_range(Spell, _, Max_Dmg),
    Spell \= heal,
    \+ secret(Warrior,Spell),
    HP =< Max_Dmg.

berserker_mode(Warrior) :-
    warrior(Warrior, HP),
    max_health(Warrior, Max_HP),
    HP < Max_HP * 0.31.

boss_choice(nuke, 1, _, _, _, 0, _).

boss_choice(heal, 0, 1, _, _, 0, _).

boss_choice(trap_key, 0, 0, 0, _, 0, 0). 

boss_choice(disable_key, 0, _, _, 0, 0, 0).

boss_choice(Spell, 0, _, _, _, 0, _) :-
    (berserker_mode(boss) -> spell_berserk(Spell) ; spell(Spell)),
    Spell \= nuke,
    Spell \= heal.

boss_choice(Spell, 0, _, _, _, 1, _) :- 
    (berserker_mode(boss) -> spell_berserk(Spell) ; spell(Spell)),
    Spell \= nuke,
    Spell \= heal.

cooldown(fireball, 2).
cooldown(ice, 3).
cooldown(lightning, 4).
cooldown(counter_spell, 0).
cooldown(summon_frog, 5).
cooldown(summon_dragon, 10).
cooldown(nuke, 20).
cooldown(heal, 3).
cooldown(trap_key, 5).
cooldown(disable_key, 10).
cooldown(berserk_fireball, 0).
cooldown(berserk_ice, 0).
cooldown(berserk_lightning, 0).
cooldown(berserk_summon_frog, 0).
cooldown(berserk_summon_dragon, 0).

initialize_cooldowns :-
    forall(spell(Spell), (
        retractall(current_cooldown(boss, Spell, _)),
        retractall(current_cooldown(you, Spell, _)),
        assertz(current_cooldown(boss, Spell, 0)),
        assertz(current_cooldown(you, Spell, 0))
    )).

initialize_cooldowns_berserk :-
    forall(spell_berserk(Spell), (
        retractall(current_cooldown(boss, Spell, _)),
        retractall(current_cooldown(you, Spell, _)),
        assertz(current_cooldown(boss, Spell, 0)),
        assertz(current_cooldown(you, Spell, 0))
    )).

update_cooldowns :-
    forall(current_cooldown(User, Spell, CD), (
        (CD > 0 -> NewCD is CD - 1; NewCD is 0),
        retract(current_cooldown(User, Spell, CD)),
        assertz(current_cooldown(User, Spell, NewCD))
    )).

update_single_cooldown(User, Spell) :-
    current_cooldown(User, Spell, CD),
    (CD > 0 -> NewCD is CD - 1; cooldown(Spell, DefaultCD), NewCD is DefaultCD),
    retract(current_cooldown(User, Spell, CD)),
    assertz(current_cooldown(User, Spell, NewCD)).

can_cast_spell(User, Spell) :-
    current_cooldown(User, Spell, CD),
    CD =:= 0.

has_mana(User, Spell) :-
    mana(User, Mana),
    mana_cost(Spell, Cost),
    Mana >= Cost.

% Se ejecuta antes de que el enemigo lance un hechizo
counter_spell(Caster, Opponent) :-
    secret(Caster, counter_spell), % Si el counter spell está activo
    retract(secret(Caster, counter_spell)), % Se elimina al activarse
    warrior(Opponent, Health),
    damage_range(counter_spell, Min, Max),
    random_between(Min, Max, Damage),
    NewHealth is max(0, Health - Damage),
    retract(warrior(Opponent, _)),
    assertz(warrior(Opponent, NewHealth)).
