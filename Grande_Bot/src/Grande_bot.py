import sc2
import random
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *


class GrandeBot(sc2.BotAI):
    def __init__(self):
        super().__init__()
        self.ONE_MINUTE = 60
        self.MAX_WORKERS = 50

    async def on_step(self, iteration):
        await self.build_workers()
        await self.distribute_workers()
        await self.build_pylons()
        await self.expand()
        await self.build_zealots()
        await self.build_stalkers()
        await self.expand()
        await self.build_assimilator()
        await self.build_gateway()
        await self.build_cybernetics_core()
        await self.build_stargate()
        await self.build_forge()
        await self.build_cannons()
        await self.stalker_attack()
        await self.zealot_attack()
        await self.base_defense()
        await self.use_abilities()

    async def use_abilities(self):
        if self.time / self.ONE_MINUTE < 2:
            nexus = self.units(UnitTypeId.NEXUS).first
            if not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                abilities = await self.get_available_abilities(nexus)
                if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities:
                    await self.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus))
        elif self.time / self.ONE_MINUTE > 2:
            unit = self.units(UnitTypeId.GATEWAY).random
            if not unit.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                abilities = await self.get_available_abilities(unit)
                if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities:
                    await self.do(unit(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, unit))

    async def build_workers(self):
        if (len(self.units(UnitTypeId.NEXUS)) * 16) > len(self.units(UnitTypeId.PROBE)) and len(self.units(UnitTypeId.PROBE)) < self.MAX_WORKERS:
            for nexus in self.units(UnitTypeId.NEXUS).ready.idle:
                if self.can_afford(UnitTypeId.PROBE) and nexus.assigned_harvesters < 17:
                    await self.do(nexus.train(UnitTypeId.PROBE))

    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(UnitTypeId.PYLON):
            for nexus in self.units(UnitTypeId.NEXUS):
                if self.can_afford(UnitTypeId.PYLON):
                    await self.build(UnitTypeId.PYLON, near=nexus)

    async def expand(self):
        if self.units(UnitTypeId.NEXUS).amount < (self.time / self.ONE_MINUTE) and self.can_afford(UnitTypeId.NEXUS):
             await self.expand_now()

    async def build_assimilator(self):
        for nexus in self.units(UnitTypeId.NEXUS).ready:
            vespenes_in_range = self.state.vespene_geyser.closer_than(15.0, nexus)
            for vespene in vespenes_in_range:
                worker = self.select_build_worker(vespene.position)
                if not self.can_afford(UnitTypeId.ASSIMILATOR) and not self.supply_left < 3:
                    break
                if worker is None:
                    break
                if not self.units(UnitTypeId.ASSIMILATOR).closer_than(1.0, vespene).exists and self.units(UnitTypeId.GATEWAY).exists:
                    if self.state.units(UnitTypeId.ASSIMILATOR).closer_than(nexus.radar_range, nexus).amount < 1:
                        await self.do(worker.build(UnitTypeId.ASSIMILATOR, vespene))

    async def build_gateway(self):
        nexuses = self.units(UnitTypeId.NEXUS).ready
        for nexus in nexuses:
            if self.units(UnitTypeId.PYLON).exists:
                pylon = self.units(UnitTypeId.PYLON).random
                if len(self.units(UnitTypeId.GATEWAY))/2 < (self.time / self.ONE_MINUTE / 2):
                    if self.can_afford(UnitTypeId.GATEWAY) and self.units(UnitTypeId.NEXUS).closer_than(10.0, pylon):
                        await self.build(UnitTypeId.GATEWAY, near=pylon)

    async def build_cybernetics_core(self):
        if not self.units(UnitTypeId.CYBERNETICSCORE):
            if self.units(UnitTypeId.PYLON).amount > 1 and self.units(UnitTypeId.GATEWAY).exists:
                pylon = self.units(UnitTypeId.PYLON).random
                if self.can_afford(UnitTypeId.CYBERNETICSCORE) and not self.already_pending(UnitTypeId.CYBERNETICSCORE):
                    await self.build(UnitTypeId.CYBERNETICSCORE, near=pylon)

    async def build_forge(self):
        if not self.units(UnitTypeId.FORGE):
            if self.units(UnitTypeId.GATEWAY).exists:
                pylon = self.units(UnitTypeId.PYLON).random
                if self.can_afford(UnitTypeId.FORGE) and not self.already_pending(UnitTypeId.FORGE):
                    await self.build(UnitTypeId.FORGE, near=pylon)

    async def build_stargate(self):
        if self.units(UnitTypeId.CYBERNETICSCORE).ready.exists:
            pylon = self.units(UnitTypeId.PYLON).random
            if len(self.units(UnitTypeId.STARGATE)) < (self.time / self.ONE_MINUTE / 4):
                if self.can_afford(UnitTypeId.STARGATE) and not self.already_pending(UnitTypeId.STARGATE):
                    await self.build(UnitTypeId.STARGATE, near=pylon)

    async def build_zealots(self):
        for gateway in self.units(UnitTypeId.GATEWAY):
            if len(self.units(UnitTypeId.STALKER)) < len(self.units(UnitTypeId.ZEALOT)):
                break
            if self.units(UnitTypeId.GATEWAY).ready.idle:
                if self.can_afford(UnitTypeId.ZEALOT) and self.supply_left > 0 and len(self.units(UnitTypeId.ZEALOT)) < (self.units(UnitTypeId.GATEWAY) * (self.time / self.ONE_MINUTE)):
                    await self.do(gateway.train(UnitTypeId.ZEALOT))

    async def build_stalkers(self):
        for gateway in self.units(UnitTypeId.GATEWAY):
            if self.can_afford(UnitTypeId.STALKER) and self.supply_left > 0 and self.units(UnitTypeId.CYBERNETICSCORE):
                if len(self.units(UnitTypeId.STALKER)) < (self.units(UnitTypeId.GATEWAY) * (self.time / self.ONE_MINUTE) * 2):
                    await self.do(gateway.train(UnitTypeId.STALKER))

    async def build_void_rays(self):
        for stargate in self.units(UnitTypeId.STARGATE):
            if self.can_afford(UnitTypeId.VOIDRAY) and self.supply_left > 0 and self.units(UnitTypeId.STARGATE).exists:
                if len(self.units(UnitTypeId.STALKER) < len(self.units(UnitTypeId.VOIDRAY))):
                    await self.do(stargate.train(UnitTypeId.VOIDRAY))

    async def stalker_attack(self):
        if self.units(UnitTypeId.STALKER).amount > 15:
            for s in self.units(UnitTypeId.STALKER).idle:
                await self.do(s.attack(self.seek_enemy(self.state)))

    async def zealot_attack(self):
        if self.units(UnitTypeId.ZEALOT).amount > 10:
            for z in self.units(UnitTypeId.ZEALOT).idle:
                await self.do(z.attack(self.seek_enemy(self.state)))

    async def base_defense(self):
        for u in self.units.idle:
            for e in self.known_enemy_units:
                if e.is_visible:
                    if len(self.known_enemy_units) > 0 and not u.type_id == UnitTypeId.PROBE and not u.is_structure:
                        await self.do(u.attack(random.choice(self.known_enemy_units)))

    async def build_cannons(self):
        if self.units(UnitTypeId.FORGE).exists:
            for n in self.units(UnitTypeId.NEXUS):
                pylon = self.units(UnitTypeId.PYLON).random
                if self.can_afford(UnitTypeId.PHOTONCANNON) and not self.already_pending(UnitTypeId.PHOTONCANNON):
                    if self.units(UnitTypeId.PHOTONCANNON).closer_than(n.radar_range, n).amount < 3:
                        await self.build(UnitTypeId.PHOTONCANNON, near=pylon)

    def seek_enemy(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]


run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, GrandeBot()),
    Computer(Race.Protoss, Difficulty.Medium)
], realtime=True)
