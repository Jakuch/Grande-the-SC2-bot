import sc2
import random
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *


class GrandeBot(sc2.BotAI):
    async def on_step(self, iteration):
        await self.build_workers()
        await self.distribute_workers()
        await self.build_pylons()
        await self.expand()
        await self.build_offensive_force()
        await self.expand()
        await self.build_assimilator()
        await self.build_gateway()
        await self.build_cybernetics_core()
        await self.stalker_attack()
        await self.zealot_attack()


    async def build_workers(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE) and nexus.assigned_harvesters < 17:
                await self.do(nexus.train(PROBE))


    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexus_list = self.units(NEXUS).ready
            for nexus in nexus_list:
                if nexus_list.exists and self.can_afford(PYLON):
                    if self.state.units(PYLON).closer_than(nexus.radar_range, nexus).amount < 4:
                        await self.build(PYLON, near=nexus_list.random)


    async def expand(self):
        nexuses = self.units(NEXUS).ready
        for nexus in nexuses:
            if self.can_afford(NEXUS) and nexus.assigned_harvesters > 13:
                supply_amount = self.supply_used
                if self.units(NEXUS).amount <= supply_amount / 16:
                    await self.expand_now()


    async def build_assimilator(self):
        for nexus in self.units(NEXUS).ready:
            vespenes_in_range = self.state.vespene_geyser.closer_than(15.0, nexus)
            for vespene in vespenes_in_range:
                if not self.can_afford(ASSIMILATOR) and not self.supply_left < 3:
                    break
                worker = self.select_build_worker(vespene.position)
                if worker is None:
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vespene).exists and self.units(GATEWAY).exists:
                    if self.state.units(ASSIMILATOR).closer_than(nexus.radar_range, nexus).amount < 2:
                        await self.do(worker.build(ASSIMILATOR, vespene))


    async def build_gateway(self):
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random
            if not self.state.units(GATEWAY).closer_than(10.0, pylon).amount > 1:
                if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                    await self.build(GATEWAY, near=pylon)


    async def build_cybernetics_core(self):
        if not self.units(CYBERNETICSCORE):
            if self.units(PYLON).amount > 1 and self.units(GATEWAY):
                pylon = self.units(PYLON).ready.random
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE) and self.units(
                        GATEWAY).amount > 1:
                    await self.build(CYBERNETICSCORE, near=pylon)


    async def build_offensive_force(self):
        for gateway in self.units(GATEWAY).ready.noqueue:
            if self.units(GATEWAY):
                if self.can_afford(ZEALOT) and self.supply_left > 0 and self.units(ZEALOT).amount < 3 * self.units(
                        GATEWAY).amount:
                    await self.do(gateway.train(ZEALOT))
                if self.can_afford(STALKER) and self.supply_left > 0 and self.units(CYBERNETICSCORE):
                    if self.units(STALKER).amount < 2 * self.units(GATEWAY).amount:
                        await self.do(gateway.train(STALKER))


    async def stalker_attack(self):
        if self.units(STALKER).amount > 15:
            for s in self.units(STALKER).idle:
                await self.do(s.attack(self.seek_enemy(self.state)))

        elif self.units(STALKER).amount > 3:
            if len(self.known_enemy_units) > 0:
                for s in self.units(STALKER).idle:
                    await self.do(s.attack(random.choice(self.known_enemy_units)))

    async def zealot_attack(self):
        if self.units(ZEALOT).amount > 10:
            for s in self.units(ZEALOT).idle:
                await self.do(s.attack(self.seek_enemy(self.state)))

        elif self.units(ZEALOT).amount > 3:
            if len(self.known_enemy_units) > 0:
                for s in self.units(ZEALOT).idle:
                    await self.do(s.attack(random.choice(self.known_enemy_units)))

    def seek_enemy(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]


run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, GrandeBot()),
    Computer(Race.Terran, Difficulty.Easy)
], realtime=True)