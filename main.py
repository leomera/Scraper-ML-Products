from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async # NOVA IMPORTAÇÃO AQUI

app = FastAPI(title="API Mercado Livre Scraper")

class ItemRequest(BaseModel):
    item_id: str

@app.post("/obter-mae")
async def get_mlb_mae(request: ItemRequest):
    item_id = request.item_id
    formatted_id = item_id.replace("MLB", "MLB-") if "-" not in item_id else item_id
    url = f"https://produto.mercadolivre.com.br/{formatted_id}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--single-process'
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        
        # APLICA A CAMUFLAGEM CONTRA O AKAMAI BOT MANAGER
        await stealth_async(page)
        
        # Bloqueia recursos visuais para acelerar e despistar
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font", "stylesheet"] else route.continue_())

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            html_content = await page.content()
            page_title = await page.title()
            
            match = re.search(r'"catalog_product_id"\s*:\s*"(MLB\d+)"', html_content)
            
            if match:
                return {
                    "item_id": item_id, 
                    "catalog_product_id": match.group(1), 
                    "titulo_pagina": page_title, 
                    "status": "sucesso"
                }
            else:
                return {
                    "item_id": item_id, 
                    "erro": "Catálogo não encontrado no HTML", 
                    "titulo_pagina": page_title, 
                    "status": "nao_encontrado"
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro no scraper: {str(e)}")
        finally:
            await browser.close()