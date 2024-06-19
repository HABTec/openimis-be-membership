from django.apps import AppConfig

MODULE_NAME = 'membership'

DEFAULT_CFG = {
}

class MembershipCardConfig(AppConfig):
    name = MODULE_NAME

    gql_query_membership_generation_perms = None #todo

    membership_slip_name = f"membershi_card" #todo, head of family name ?
    wkhtml_cmd_options_for_printing = {
        # 'margin-top': 3,
        "orientation": "Portrait",
        "page-size": "A4",
        "no-outline": None,
        "encoding": "UTF-8",
        "enable-local-file-access": True,
        "margin-top": "0",
        "margin-bottom": "0",
        'disable-smart-shrinking': False,
        "quiet": True,
    }
    @staticmethod
    def get_template_by_os():
        import platform
        system = platform.system()
        if system == "Windows":
            template_name = "card_template_osx.html" #not tested for windows
        elif system == "Darwin":
            template_name = "card_template_linux.html"
        elif system == "Linux":
            template_name = "card_template_linux.html"
        else:
            return None
        return template_name

    @staticmethod
    def get_terms_and_conditions(language='en'):
        conditions = {
            'en': [
                "All citizens are required to register for a national identification card within 30 days of turning 18 years old.",
                "Employers must verify the identification and legal work status of all employees before hiring.",
                "All citizens must report any changes of address to the government within 10 days of moving.",
                "Individuals must renew their identification cards every 5 years to ensure that the information remains current.",
                "The government provides subsidies for low-income families to help cover the cost of obtaining identification cards."
            ],
            'es': [
                "Todos los ciudadanos están obligados a registrarse para obtener una tarjeta de identificación nacional dentro de los 30 días posteriores a cumplir 18 años.",
                "Los empleadores deben verificar la identificación y el estado legal de trabajo de todos los empleados antes de contratarlos.",
                "Todos los ciudadanos deben informar cualquier cambio de dirección al gobierno dentro de los 10 días posteriores a la mudanza.",
                "Las personas deben renovar sus tarjetas de identificación cada 5 años para asegurar que la información se mantenga actualizada.",
                "El gobierno proporciona subsidios para familias de bajos ingresos para ayudar a cubrir el costo de obtener tarjetas de identificación."
            ],
            'fr': [
                "Tous les citoyens sont tenus de s'inscrire pour une carte d'identité nationale dans les 30 jours suivant leur 18e anniversaire.",
                "Les employeurs doivent vérifier l'identification et le statut légal de travail de tous les employés avant de les embaucher.",
                "Tous les citoyens doivent signaler tout changement d'adresse au gouvernement dans les 10 jours suivant le déménagement.",
                "Les individus doivent renouveler leurs cartes d'identité tous les 5 ans pour garantir que les informations restent à jour.",
                "Le gouvernement offre des subventions aux familles à faible revenu pour aider à couvrir le coût de l'obtention des cartes d'identité."
            ]
            # Add more languages as needed
        }
        return conditions.get(language, conditions['en'])

