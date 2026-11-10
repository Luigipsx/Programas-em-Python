class ValidationError(ValueError):
    """Erro de domínio que pode ser exibido ao usuário."""


class StorageError(RuntimeError):
    """Erro de persistência sem detalhes de conexão."""
