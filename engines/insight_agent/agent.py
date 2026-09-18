import asyncio

from engines.common.llm_client import LLMClient
from engines.insight_agent.context import InsightContext
from engines.insight_agent.graph import build_graph


async def invoke_insight_agent(query: str,
                               role: str,
                               llm_client: LLMClient,
                               out_put_dir: str,
                               process_callback
                               ):
    pass


if __name__ == '__main__':


   async def main_test():
       context = InsightContext(
           role="insight",
           llm_client=LLMClient.from_role("insight"),
           output_dir="",
           progress_callback=None,
       )
       graph = build_graph(context)

       initial_state = {"query": "高考难吗", "role": "insight"}

       await graph.ainvoke(initial_state)


   asyncio.run(main_test())




