# 客户档案

使用本 Skill 的 `assets/client_profile.template.json`。核心字段是目标、读者、品牌、行业、业务类型、服务范围、服务/产品、证据、渠道和行业敏感度。

证据条目分别保存 source、fact、date、url 或 evidence_path、status。只有状态标为 verified 且定位字段完整的条目计入“声明已核验”；脚本不验证真假。

先向用户询问缺少的字段，分轮收集；已提供的信息不重复询问，不预填业务类型、地区或客户阶段。空值和“待补充……”不计完整度。虚构示例明确 is_demo=true，不混入真实项目。
