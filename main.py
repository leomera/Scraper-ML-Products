from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
from playwright.async_api import async_playwright

app = FastAPI(title="API Mercado Livre Scraper")

# Define o formato que o n8n vai mandar (um JSON com o item_id)
class ItemRequest(BaseModel):
    item_id: str

@app.post("/obter-mae")
async def get_mlb_mae(request: ItemRequest):
    item_id = request.item_id
    formatted_id = item_id.replace("MLB", "MLB-") if "-" not in item_id else item_id
    url = f"https://produto.mercadolivre.com.br/{formatted_id}"

    async with async_playwright() as p:
        # Lança o navegador com flags para rodar em servidores na nuvem
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        
        page = await context.new_page()
        
        # Bloqueia o carregamento de imagens e CSS para a requisição voar
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font", "stylesheet"] else route.continue_())

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            html_content = await page.content()
            
            # Executa o regex para encontrar o catálogo
            match = re.search(r'"catalog_product_id":"(MLB\d+)"', html_content)
            
            if match:
                return {"item_id": item_id, "catalog_product_id": match.group(1), "status": "sucesso"}
            else:
                return {"item_id": item_id, "erro": "Catálogo não encontrado no HTML", "status": "nao_encontrado"}
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro no scraper: {str(e)}")
        finally:
            await browser.close()