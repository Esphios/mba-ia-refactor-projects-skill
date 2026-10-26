CATEGORIES = ('informatica', 'moveis', 'vestuario', 'geral', 'eletronicos', 'livros')
DEFAULT_CATEGORY = 'geral'
ORDER_STATUSES = ('pendente', 'aprovado', 'enviado', 'entregue', 'cancelado')
DISCOUNT_TIERS = ((10000, .1), (5000, .05), (1000, .02))
SQLITE_MAX_INTEGER = 9223372036854775807


def sqlite_integer(value):
    return type(value) is int and -SQLITE_MAX_INTEGER - 1 <= value <= SQLITE_MAX_INTEGER


def sales_summary(totals):
    count, revenue, pending, approved, cancelled = totals
    revenue = revenue if revenue is not None else 0
    discount = next((revenue * rate for threshold, rate in DISCOUNT_TIERS if revenue > threshold), 0)
    return {'total_pedidos': count, 'faturamento_bruto': round(revenue, 2),
        'desconto_aplicavel': round(discount, 2), 'faturamento_liquido': round(revenue-discount, 2),
        'pedidos_pendentes': pending or 0, 'pedidos_aprovados': approved or 0,
        'pedidos_cancelados': cancelled or 0, 'ticket_medio': round(revenue/count, 2) if count else 0}
