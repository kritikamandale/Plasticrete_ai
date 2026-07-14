"""
Contract tests: public API import surface and dataclass shape for M4.
"""
import dataclasses


class TestPublicImport:
    def test_can_import_public_functions(self):
        from modules.m4_recommendation import load_models, recommend
        assert callable(load_models)
        assert callable(recommend)

    def test_no_circular_import(self):
        import importlib
        import modules.m4_recommendation as m4
        importlib.reload(m4)


class TestSchemaDataclasses:
    def test_recommendation_result_fields(self):
        from modules.m4_recommendation.utils.schema import RecommendationResult
        field_names = {f.name for f in dataclasses.fields(RecommendationResult)}
        required = {
            "primary_application", "primary_confidence_pct",
            "suitable_applications", "suitability_scores",
            "cost_benefit", "rag_analogues",
        }
        assert required == field_names

    def test_cost_benefit_fields(self):
        from modules.m4_recommendation.utils.schema import CostBenefit
        field_names = {f.name for f in dataclasses.fields(CostBenefit)}
        required = {
            "plastic_mix_cost_inr_m3", "conventional_cost_inr_m3",
            "cost_saving_inr_m3", "cost_saving_pct",
            "plastic_mix_cost_inr_m2", "conventional_cost_inr_m2",
            "cost_saving_inr_m2", "product_yield_m2_per_m3",
            "plastic_kg_per_m3", "additive_kg_per_m3",
        }
        assert required == field_names

    def test_rag_analogue_fields(self):
        from modules.m4_recommendation.utils.schema import RAGAnalogue
        field_names = {f.name for f in dataclasses.fields(RAGAnalogue)}
        required = {
            "rank", "id", "author", "year", "journal", "doi",
            "primary_application", "secondary_application",
            "l2_distance", "properties",
        }
        assert required == field_names
