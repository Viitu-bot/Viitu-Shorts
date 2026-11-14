# Viitu Shorts — automação

Ferramentas locais (Windows) para o canal Viitu Shorts.

| Pasta | O que é |
|---|---|
| `pesquisa/protocolo_mineracao_temas.md` | Método para escolher subnicho e temas validados + prompts prontos para o Gemini |
| `radar/` | Script que mede os números reais dos canais (outliers) — sem chave de API |

## Instalação no Windows (uma vez)

1. Instale o Python 3.11+ em https://www.python.org/downloads/ e **marque "Add Python to PATH"** na instalação.
2. Baixe este repositório (botão verde **Code → Download ZIP** no GitHub) e descompacte.
3. Abra a pasta, clique na barra de endereço, digite `cmd` e aperte Enter.
4. Rode:
   ```
   pip install -r requirements.txt
   ```

## Usar o radar

```
python radar/radar.py canais radar/canais.txt
python radar/radar.py buscar radar/buscas.txt
```
Os resultados saem em `radar/saida/` como `.csv` (abre no Excel ou no Google Sheets).

Se aparecer erro 429 ou "Sign in to confirm you're not a bot", espere uns minutos ou rode com menos canais.
Se persistir, atualize: `pip install -U yt-dlp`.
