class KSeFHeaders:
    @staticmethod
    def bearer(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def problem_details() -> dict[str, str]:
        return {"X-Error-Format": "problem-details"}
