from langchain_gigachat import GigaChat

from config_data.config import Config, load_config

config: Config = load_config()


class GigaChatGateway:
    def __init__(self, tools=None):
        self.creds = config.giga_connector.giga_creds
        self.model = config.giga_connector.giga_model
        self.giga = GigaChat(
            credentials=self.creds,
            model=self.model,
            verify_ssl_certs=False,
        )
        if tools:
            self.giga = self.giga.bind_tools(tools)

    async def send_to_llm(self, messages):
        response = await self.giga.ainvoke(messages)

        return response
