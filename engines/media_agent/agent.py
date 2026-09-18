from engines.common.llm_client import LLMClient


async def invoke_media_agent(query: str,
                             role: str,
                             llm_client: LLMClient,
                             out_put_dir: str,
                             process_callback=lambda update: {update}
                             ):
    pass
