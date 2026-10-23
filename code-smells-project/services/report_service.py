from models.report_model import ReportModel


DISCOUNT_TIERS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))


def calculate_discount(revenue):
    for threshold, rate in DISCOUNT_TIERS:
        if revenue > threshold:
            return revenue * rate
    return 0


class ReportService:
    def sales_report(self):
        totals = ReportModel().sales_totals()
        revenue = totals["faturamento"]
        discount = calculate_discount(revenue)
        count = totals["total_pedidos"]
        return {
            "total_pedidos": count,
            "faturamento_bruto": round(revenue, 2),
            "desconto_aplicavel": round(discount, 2),
            "faturamento_liquido": round(revenue - discount, 2),
            "pedidos_pendentes": totals["pendentes"],
            "pedidos_aprovados": totals["aprovados"],
            "pedidos_cancelados": totals["cancelados"],
            "ticket_medio": round(revenue / count, 2) if count else 0,
        }
