"""Regression checks for evidence boundaries and interoperability, with synthetic inputs."""
from __future__ import annotations
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "skills" / "doubao-geo-publisher" / "scripts"
sys.path.insert(0, str(PUB))
import geo_core
import diagnose_client
import generate_geo_plan
import build_prompt_packet
import run_closed_loop_demo


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = load_module("adapter", "skills/geo-platform-adapter/scripts/adapt_platform_versions.py")
research = load_module("research", "skills/geo-doubao-research/scripts/build_doubao_research_report.py")
miner = load_module("miner", "skills/geo-keyword-miner/scripts/generate_keyword_table.py")


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.out = Path(self.temporary.name)
        self.profile = geo_core.read_json(ROOT / "examples/local-service/client_profile.json")

    def test_missing_articles_never_pass(self):
        result = run_closed_loop_demo.lint_articles(None, None, "general", self.out)
        self.assertEqual(result["status"], "skipped")
        self.assertIsNone(result["passed"])
        empty = self.out / "empty"
        empty.mkdir()
        result = run_closed_loop_demo.lint_articles(empty, None, "general", self.out)
        self.assertEqual(result["status"], "empty")
        self.assertIsNone(result["passed"])

    def test_blank_profile_only_produces_questions(self):
        blank = ROOT / "skills/doubao-geo-publisher/assets/client_profile.template.json"
        output = self.out / "intake"
        result = run_closed_loop_demo.run(blank, output)
        self.assertEqual(result["overall_status"], "incomplete")
        self.assertEqual(result["input_status"], "needs_input")
        self.assertFalse(result["planning_generated"])
        self.assertEqual(result["keyword_count"], 0)
        self.assertEqual({p.name for p in output.iterdir()}, {
            "diagnosis.json", "diagnosis.md", "intake-questions.json", "intake-questions.md",
            "showcase-summary.json", "showcase-summary.md",
        })
        report = geo_core.read_json(output / "diagnosis.json")
        self.assertEqual(report["readiness_score"], 0)
        self.assertEqual(report["scenario"], "待向用户确认")
        self.assertEqual(len(report["client_intake"]["questions"]), 7)
        command = [sys.executable, str(PUB / "run_closed_loop_demo.py"), "--profile", str(blank),
                   "--output-dir", str(self.out / "intake-cli")]
        process = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(process.returncode, 2, process.stderr)

    def test_generation_does_not_invent_missing_client_context(self):
        for field in ("brand_name", "industry", "business_type", "service_area", "core_services"):
            profile = dict(self.profile, **{field: ""})
            if field == "service_area":
                profile.pop("primary_city", None)
            with self.assertRaises(geo_core.ClientInputRequired, msg=field):
                miner.generate(profile, 24)
        profile = dict(self.profile, objectives=[], target_customers=[])
        self.assertTrue(miner.generate(profile, 2))
        with self.assertRaises(geo_core.ClientInputRequired):
            generate_geo_plan.build_plan(profile)
        with self.assertRaises(geo_core.ClientInputRequired):
            build_prompt_packet.build_prompt(profile, "查询", "selection", "sohu")

    def test_intake_only_asks_missing_fields_and_accepts_products(self):
        profile = dict(self.profile, business_type="待确认", core_services=[], core_products=["测试产品"])
        original = json.dumps(profile, ensure_ascii=False, sort_keys=True)
        intake = geo_core.client_intake(profile)
        self.assertEqual(intake["missing_fields"], ["business_type"])
        self.assertEqual([q["field"] for q in intake["questions"]], ["business_type"])
        self.assertEqual(json.dumps(profile, ensure_ascii=False, sort_keys=True), original)
        profile["business_type"] = "national_brand"
        self.assertEqual(geo_core.client_intake(profile)["status"], "ready")
        report = diagnose_client.build_report(profile)
        self.assertNotIn("production.offerings", report["missing_fields"])
        self.assertTrue(miner.generate(profile, 2))
        profile["client_stage"] = ""
        self.assertEqual(run_closed_loop_demo.monitoring_plan(profile, None)["cadence"]["status"], "needs_input")
        profile["core_products"] = []
        profile["business_desc"] = "用户提供的业务描述"
        prompt = build_prompt_packet.build_prompt(profile, "问题", "selection", "sohu")
        self.assertIn("服务或业务描述：用户提供的业务描述", prompt)

    def test_missing_client_cli_does_not_write_generated_outputs(self):
        blank = ROOT / "skills/doubao-geo-publisher/assets/client_profile.template.json"
        commands = [
            [ROOT / "skills/geo-keyword-miner/scripts/generate_keyword_table.py", "--profile", blank],
            [PUB / "generate_geo_plan.py", "--input", blank],
            [PUB / "build_prompt_packet.py", "--profile", blank, "--keyword", "查询",
             "--article-type", "selection", "--platform", "sohu"],
        ]
        for index, args in enumerate(commands):
            output = self.out / f"unexpected-{index}.txt"
            result = subprocess.run([sys.executable] + [str(x) for x in args] + ["--output", str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("请先向用户询问", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_workflow_preserves_existing_output_directory(self):
        (self.out / "previous.txt").write_text("earlier result", encoding="utf-8")
        with self.assertRaises(ValueError):
            run_closed_loop_demo.run(ROOT / "examples/local-service/client_profile.json", self.out)
        self.assertEqual(list(self.out.iterdir()), [self.out / "previous.txt"])

    def test_adapter_outputs_are_actually_checked(self):
        source = "# 服务怎么选\n\n客户资料显示，服务需要按范围判断。"
        variants = self.out / "platforms"
        report = adapter.adapt(source, variants)
        self.assertFalse(report["passed"])
        result = run_closed_loop_demo.lint_articles(variants, None, "general", self.out)
        self.assertEqual(len(result["articles"]), 4)
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["passed"])

    def test_failed_checks_still_write_summary(self):
        variants = self.out / "bad"
        adapter.adapt("# 主稿\n\n客户资料显示，这是测试正文。", variants)
        result = run_closed_loop_demo.run(ROOT / "examples/local-service/client_profile.json",
                                         self.out / "result", variants)
        self.assertEqual(result["overall_status"], "failed")
        self.assertTrue((self.out / "result/showcase-summary.md").is_file())

    def test_unrecognized_and_missing_manifest_articles_fail(self):
        articles = self.out / "articles"
        articles.mkdir()
        (articles / "unknown.md").write_text("# 标题\n\n正文", encoding="utf-8")
        geo_core.write_json(articles / "article-manifest.json", [{"file": "missing.md", "platform": "sohu"}])
        result = run_closed_loop_demo.lint_articles(articles, None, "general", self.out)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(result["errors"]), 2)

    def test_settings_are_not_published(self):
        for suffix in ("", "\n---\n", "\n## 正文补充\n公开内容"):
            text = "# 标题\n\n公开正文\n\n## 发布设置（不复制到正文）\nGEO 客户资料显示\n参考来源：材料目录\n" + suffix
            variants = self.out / str(len(suffix))
            result = adapter.adapt(text, variants)
            self.assertTrue(result["passed"])
            for path in variants.glob("*.md"):
                body = path.read_text(encoding="utf-8")
                self.assertNotIn("GEO", body)
                self.assertNotIn("客户资料显示", body)
            self.assertIn("参考来源", (variants / "article.sources.txt").read_text(encoding="utf-8"))
            check = run_closed_loop_demo.lint_articles(variants, None, "general", self.out)
            self.assertFalse(any(i["code"] == "evidence_missing" for a in check["articles"] for i in a["issues"]))

    def test_no_forced_year_number_or_keyword_density(self):
        issues = geo_core.check_article("服务机构是谁", "这里说明机构与业务的关系。",
                                        "toutiao", keyword="机构选择", evidence="材料来源")
        self.assertFalse(any(i["severity"] == "error" for i in issues))
        self.assertEqual(geo_core.neutral_title("服务机构是谁", "toutiao"), "服务机构是谁")

    def test_missing_unknown_and_partial_comparisons(self):
        yes, no, unknown, partial = ({"target_brand_seen": value} for value in ("yes", "no", "unknown", "partial"))
        for before, after in ((None, yes), (yes, None), (unknown, yes), (yes, unknown), (unknown, unknown)):
            self.assertEqual(research.compare_status(before, after, "品牌")[2], "不可比较")
        self.assertEqual(research.compare_status(no, yes, "品牌")[2], "改善")
        self.assertEqual(research.compare_status(partial, no, "品牌")[2], "回落")
        self.assertEqual(research.normalize_seen("unknown", "品牌确实出现在文字里", "品牌"), "待人工判断")

    def test_comparison_rejects_brand_mix_and_duplicate_queries(self):
        with self.assertRaises(ValueError):
            research.comparison_report({"brand_name": "甲"}, [], {"brand_name": "乙"}, [])
        rows = [{"keyword": "同一问题"}, {"keyword": "同一问题"}]
        with self.assertRaises(ValueError):
            research.comparison_report({"brand_name": "甲"}, rows, {"brand_name": "甲"}, [])

    def test_empty_templates_are_not_observations(self):
        text = (ROOT / "templates/effect-log.template.md").read_text(encoding="utf-8")
        self.assertEqual(research.parse_records(text, "effect")[1], [])

    def test_answer_headings_do_not_create_extra_queries(self):
        text = "## Query: 实际问题\n- target_brand_seen: yes\n```answer\n## Query: 回答里的示例标题\n这是回答正文\n```\n"
        _, records = research.parse_records(text, "effect")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["keyword"], "实际问题")
        self.assertIn("回答里的示例标题", records[0]["answer"])

    def test_synthetic_and_observed_records_cannot_be_mixed(self):
        with self.assertRaises(ValueError):
            research.comparison_report({"brand_name": "品牌", "data_kind": "synthetic"}, [],
                                       {"brand_name": "品牌", "data_kind": "observed"}, [])

    def test_placeholders_do_not_count_as_evidence(self):
        for value in ("待补充", "待补充可核查证据", "待填写来源", "TODO fact", "示例资质"):
            self.assertFalse(geo_core.has_value(value), value)
        self.profile["is_demo"] = False
        self.profile["eeat"] = {k: ["待补充可核查证据"] for k in ("expertise", "experience", "authority", "trust")}
        self.profile["verified_sources"] = [{"source": "待补充来源", "fact": "待补充事实", "status": "verified"}]
        result = diagnose_client.build_report(self.profile)
        self.assertLess(result["readiness_score"], 100)
        self.assertEqual(result["evidence_review"]["status"], "unverified")
        self.assertFalse(result["ready_for_editorial_review"])

    def test_demo_and_declared_verified_are_distinct(self):
        self.profile["verified_sources"] = [{"source": "材料甲", "fact": "有定位的测试事实",
                                             "evidence_path": "sample.txt", "status": "verified"}]
        self.assertEqual(geo_core.evidence_summary(self.profile)["status"], "synthetic")
        self.profile["is_demo"] = False
        self.assertEqual(geo_core.evidence_summary(self.profile)["status"], "declared_verified")
        self.profile["verified_sources"][0]["evidence_path"] = ""
        self.assertEqual(geo_core.evidence_summary(self.profile)["status"], "unverified")

    def test_common_enums_keywords_and_article_aliases(self):
        chinese = dict(self.profile, business_type="本地B2C")
        self.assertEqual(miner.generate(chinese, 24), miner.generate(self.profile, 24))
        with self.assertRaises(ValueError):
            miner.generate(dict(self.profile, business_type="typo"), 24)
        words = [r["核心关键词"] for r in miner.generate(self.profile, 24)]
        self.assertIn("演示市家庭保洁怎么选", words)
        self.assertFalse(any("怎么选怎么选" in w or "演示市演示市" in w for w in words))
        plan = generate_geo_plan.build_plan(self.profile)
        self.assertEqual(set(words), {r["keyword"] for b in plan["keyword_buckets"].values() for r in b})
        prompt = build_prompt_packet.build_prompt(self.profile, "查询", "guide", "toutiao")
        self.assertIn("选择判断型", prompt)
        self.assertNotIn("选购指南", prompt)

    def test_hybrid_limit_contains_multiple_formulas(self):
        rows = miner.generate(dict(self.profile, business_type="hybrid"), 8)
        self.assertTrue({"本地公式", "全国公式", "B2B公式"}.issubset({r["公式类型"] for r in rows}))

    def test_platform_validation_precedes_output_writes(self):
        with self.assertRaises(ValueError):
            adapter.adapt("# 标题\n\n正文", self.out / "invalid", platforms=["../escape"])
        self.assertFalse((self.out / "invalid").exists())

    def test_offline_demo_end_to_end(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/run_offline_demo.py"),
                                 "--output-dir", str(self.out / "demo")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = geo_core.read_json(self.out / "demo/showcase/showcase-summary.json")
        self.assertEqual(summary["article_count"], 4)
        self.assertEqual(summary["overall_status"], "passed")
        self.assertEqual(summary["search_effect_status"], "not_evaluated")
        comparison = (self.out / "demo/comparison.md").read_text(encoding="utf-8")
        self.assertIn("- 改善: 1", comparison)
        self.assertIn("- 不可比较: 2", comparison)

    def test_installed_suite_and_existing_files_are_preserved(self):
        destination = self.out / "installed"
        command = [sys.executable, str(ROOT / "scripts/install_skills.py"), "--destination", str(destination)]
        first = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        entry = destination / "doubao-geo-publisher/scripts/run_closed_loop_demo.py"
        result = subprocess.run([sys.executable, str(entry), "--profile",
                                 str(ROOT / "examples/local-service/client_profile.json"),
                                 "--output-dir", str(self.out / "installed-run")],
                                cwd=self.out, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        original = entry.read_bytes()
        second = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(entry.read_bytes(), original)

    @unittest.skipUnless(os.name == "posix", "Shell wrappers are optional on Windows.")
    def test_browser_wrappers_use_explicit_installed_binary(self):
        stub = self.out / "playwright"
        stub.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n", encoding="utf-8")
        stub.chmod(0o755)
        env = dict(os.environ, PLAYWRIGHT_BIN=str(stub))
        script = ROOT / "skills/geo-doubao-research/scripts/prepare_doubao_session.sh"
        result = subprocess.run(["bash", str(script), "--profile-dir", str(self.out / "profile with spaces")],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("codegen", result.stdout)
        self.assertIn(str(self.out / "profile with spaces"), result.stdout)


if __name__ == "__main__":
    unittest.main()
