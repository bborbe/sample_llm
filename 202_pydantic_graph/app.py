from __future__ import annotations
from dataclasses import dataclass
import logfire
from devtools import debug
from dotenv import load_dotenv
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()


@dataclass
class DivisibleBy5(BaseNode[None, None, int]):
    foo: int

    async def run(
            self,
            ctx: GraphRunContext,
    ) -> Increment | End[int]:
        if self.foo % 5 == 0:
            return End(self.foo)
        else:
            return Increment(self.foo)


@dataclass
class Increment(BaseNode):
    foo: int

    async def run(self, ctx: GraphRunContext) -> DivisibleBy5:
        return DivisibleBy5(self.foo + 1)


fives_graph = Graph(nodes=[DivisibleBy5, Increment])
result, history = fives_graph.run_sync(DivisibleBy5(1))
print(result)
debug([item.data_snapshot() for item in history])
