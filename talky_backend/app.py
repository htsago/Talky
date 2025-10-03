import logging
import json
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import uvicorn

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GenerateRequest(BaseModel):
    details: Dict[str, Any]

class CorrectedDetails(BaseModel):
    numero: int | str = Field(description="Le numéro de l'acte, doit être un entier.")
    theme: str = Field(description="Le thème principal du talk-show.")
    date: str = Field(description="La date de l'événement.")
    horaire: str = Field(description="L'horaire ou la plage horaire.")
    lieu: str = Field(description="Le lieu de l'événement.")

def get_corrector_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system",
         """
        Tu es un assistant qui nettoie et valide des données JSON pour un programme de talk-show.
        Ton objectif est de corriger les erreurs de frappe, de standardiser les formats et de rendre les données cohérentes.
        Les règles sont :
        - Le champ 'numero' doit être un entier. S'il contient du texte ou est invalide, remplace-le par 1.
        - Le champ 'horaire' doit être un intervalle de temps clair.
        - Les autres champs ('theme', 'date', 'lieu') doivent être conservés mais nettoyés de toute erreur évidente.
        - Tu dois répondre UNIQUEMENT avec un objet JSON. N'ajoute aucun commentaire, texte ou formatage markdown.
        """
        ),
        ("human", "Voici le JSON à corriger : {user_details}")
    ])

def get_talkshow_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_template(
    """
    Tu es un assistant qui génère un programme de Talk-Show en respectant ce format :

    **TALK ACTE {numero} — Débats : {theme}**

    📅 {date}
    ⏰ {horaire}
    📍 {lieu}
    Petite Intro max une phrase qui présente le sujet!
    🔥 **Au programme :**
    ✅ une question pertinente et provocante liée au thème.
    ✅ une question pertinente et provocante liée au thème.
    ✅ une question pertinente et provocante liée au thème.
    ✅ une question pertinente et provocante liée au thème.

    📲 RDV {date} de {horaire} ! Prépare tes questions. (Si l'horaire est une plage, reformule-le sous la forme "de HH:MM à HH:MM")

    Instructions supplémentaires :
    - Les emojis doivent être générés par toi de manière pertinente.
    - Respecte scrupuleusement le format ci-dessus, en utilisant markdown pour le gras (**texte**) et les listes (* point).
    - Les thèses doivent être des affirmations claires, concises et conçues pour susciter le débat sur le thème donné, sans être des conseils pratiques.
    - Envoie uniquement le message !
    - Ne jamais écrire en italique !
    """
    )

class LLMService:
    def __init__(self, model: str = "groq/compound"):
        self.llm = ChatGroq(model=model, temperature=0.7)
        self.corrector_chain = self._create_corrector_chain()
        self.talkshow_chain = self._create_talkshow_chain()

    def _create_corrector_chain(self) -> Runnable:
        prompt = get_corrector_prompt()
        parser = JsonOutputParser(pydantic_object=CorrectedDetails)
        return prompt | self.llm | parser

    def _create_talkshow_chain(self) -> Runnable:
        prompt = get_talkshow_prompt()
        return prompt | self.llm

    async def run_corrector(self, user_details: Dict[str, Any]) -> CorrectedDetails:
        try:
            details_str = json.dumps(user_details)
            return await self.corrector_chain.ainvoke({"user_details": details_str})
        except Exception as e:
            logger.warning(f"La chaîne de correction a échoué: {e}. Utilisation des données originales.")
            try:
                user_details['numero'] = int(user_details.get('numero', 1))
            except (ValueError, TypeError):
                user_details['numero'] = 1
            return CorrectedDetails.parse_obj(user_details)

    async def run_talkshow_generator(self, details: CorrectedDetails) -> str:
        result = await self.talkshow_chain.ainvoke(details)
        return result.content if hasattr(result, "content") else str(result)

app = FastAPI(
    title="Talk Show Generator API",
    version="1.1",
    description="Une API pour générer des programmes de talk-show à partir de détails fournis."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
llm_service = LLMService()

@app.post("/generate", summary="Génère un programme de talk-show")
async def generate_endpoint(payload: GenerateRequest):
    try:
        corrected_details = await llm_service.run_corrector(payload.details)
        output = await llm_service.run_talkshow_generator(corrected_details)
        return {"message": output}
    except Exception as e:
        logger.error(f"Erreur inattendue dans l'endpoint /generate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Une erreur interne est survenue: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8081)