//! st.phenomenon.v1 指令 → 表现参数（纯函数变换）。
//!
//! 边界（01-Architecture 第三节「现象由状态派生」）：
//!   - 输入只有现象指令 JSON；WASM 只认指令 ID、类别与 physics 表现量。
//!   - 不认分子、不认求解细节、不复算任何化学量——pH / ΔT / 指示剂比值一律取指令原值。
//!   - intensity 已是求解层归一化的表现强度，此处只做颜色插值与强度映射。
//!   - 不绘制 Canvas（绘制归 web-ui 的 PixiJS 层）。
//!
//! 输出 `st.appearance.v1`：液体 RGBA + 现象效果列表 + 可见类别集合。

use wasm_bindgen::prelude::*;
use serde_json::{json, Value};

/// 命名颜色 → RGBA（0-255）。表现层色表，不进化学事实层。
/// 无色用 alpha=0 的透明白表示，便于插值出「由无色渐显」的效果。
fn named_color(name: &str) -> [f64; 4] {
    match name.trim().to_ascii_lowercase().as_str() {
        "red" => [255.0, 0.0, 0.0, 1.0],
        "yellow" => [255.0, 255.0, 0.0, 1.0],
        "pink" => [255.0, 192.0, 203.0, 1.0],
        "colorless" | "transparent" | "none" => [255.0, 255.0, 255.0, 0.0],
        "orange" => [255.0, 165.0, 0.0, 1.0],
        "blue" => [0.0, 0.0, 255.0, 1.0],
        "green" => [0.0, 128.0, 0.0, 1.0],
        "purple" => [128.0, 0.0, 128.0, 1.0],
        "brown" => [165.0, 42.0, 42.0, 1.0],
        "white" => [255.0, 255.0, 255.0, 1.0],
        "black" => [0.0, 0.0, 0.0, 1.0],
        _ => [255.0, 255.0, 255.0, 0.0], // 未知色诚实降级为透明，不臆造颜色
    }
}

/// 线性插值 acid ↔ base，t=intensity(fraction_base)∈[0,1]。
fn lerp_rgba(acid: [f64; 4], base: [f64; 4], t: f64) -> [f64; 4] {
    let t = t.clamp(0.0, 1.0);
    [
        acid[0] + (base[0] - acid[0]) * t,
        acid[1] + (base[1] - acid[1]) * t,
        acid[2] + (base[2] - acid[2]) * t,
        acid[3] + (base[3] - acid[3]) * t,
    ]
}

/// source-over alpha 合成：把 src 叠到 dst 上（多条指示剂叠加）。
fn alpha_over(dst: [f64; 4], src: [f64; 4]) -> [f64; 4] {
    let sa = src[3].clamp(0.0, 1.0);
    let da = dst[3].clamp(0.0, 1.0);
    let oa = sa + da * (1.0 - sa);
    if oa <= 0.0 {
        return [255.0, 255.0, 255.0, 0.0];
    }
    let mix = |s: f64, d: f64| (s * sa + d * da * (1.0 - sa)) / oa;
    [mix(src[0], dst[0]), mix(src[1], dst[1]), mix(src[2], dst[2]), oa]
}

fn rgba_json(c: [f64; 4]) -> Value {
    json!([
        c[0].round() as u8,
        c[1].round() as u8,
        c[2].round() as u8,
        (c[3].clamp(0.0, 1.0) * 1000.0).round() / 1000.0,
    ])
}

fn as_f64(v: Option<&Value>) -> Option<f64> {
    v.and_then(Value::as_f64).or_else(|| v.and_then(Value::as_i64).map(|i| i as f64))
}

fn as_str<'a>(v: Option<&'a Value>, key: &str) -> Option<&'a str> {
    v.and_then(|o| o.get(key)).and_then(Value::as_str)
}

/// 纯变换：现象指令数组 → 表现参数对象。对非法/未知指令跳过，不崩。
pub fn transform(directives: &[Value]) -> Value {
    let mut liquid: [f64; 4] = [255.0, 255.0, 255.0, 0.0]; // 基础：空容器透明
    let mut effects: Vec<Value> = Vec::new();
    let mut visible: Vec<String> = Vec::new();
    let mut container_id = String::new();

    for d in directives {
        let dtype = as_str(Some(d), "type").unwrap_or("");
        if let Some(cid) = as_str(Some(d), "container_id") {
            if container_id.is_empty() {
                container_id = cid.to_string();
            }
        }
        let intensity = as_f64(d.get("intensity")).unwrap_or(0.5).clamp(0.0, 1.0);
        if !visible.iter().any(|x| x == dtype) && !dtype.is_empty() {
            visible.push(dtype.to_string());
        }

        match dtype {
            "color_change" => {
                let acid = as_str(d.get("physics"), "acid_color").unwrap_or("colorless");
                let base = as_str(d.get("physics"), "base_color").unwrap_or("colorless");
                let color = lerp_rgba(named_color(acid), named_color(base), intensity);
                liquid = alpha_over(liquid, color);
            }
            "temperature_change" => {
                let delta = as_f64(d.get("physics").and_then(|p| p.get("delta_K"))).unwrap_or(0.0);
                effects.push(json!({
                    "type": "temperature_change",
                    "intensity": intensity,
                    "delta_K": delta,
                    "hot": delta >= 0.0,
                }));
            }
            "splash" => {
                effects.push(json!({
                    "type": "splash",
                    "intensity": intensity,
                }));
            }
            // 其余已注册类别本切片不绘制，但仍在 visible 中如实列出（不臆造表现）。
            _ => {}
        }
    }

    json!({
        "schema_version": "st.appearance.v1",
        "container_id": container_id,
        "liquid": { "rgba": rgba_json(liquid) },
        "effects": effects,
        "visible": visible,
    })
}

/// WASM 导出入口：接收指令 JSON 字符串，返回表现参数 JSON 字符串。
#[wasm_bindgen]
pub fn transform_json(directives_json: &str) -> String {
    let directives: Vec<Value> = serde_json::from_str(directives_json).unwrap_or_default();
    transform(&directives).to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn directive(dtype: &str, intensity: f64, physics: Value) -> Value {
        json!({
            "schema_version": "st.phenomenon.v1",
            "directive_id": format!("d-{}", dtype),
            "container_id": "beaker-1",
            "type": dtype,
            "timestamp_ms": 0,
            "intensity": intensity,
            "physics": physics,
        })
    }

    #[test]
    fn empty_input_no_phenomenon() {
        let out = transform(&[]);
        assert_eq!(out["liquid"]["rgba"][3], 0.0);
        assert_eq!(out["visible"].as_array().unwrap().len(), 0);
        assert_eq!(out["effects"].as_array().unwrap().len(), 0);
    }

    #[test]
    fn color_lerp_boundaries() {
        let ph = json!({"acid_color": "red", "base_color": "yellow"});
        // intensity=0 → 全酸式红
        let a = transform(&[directive("color_change", 0.0, ph.clone())]);
        assert_eq!(a["liquid"]["rgba"][0], 255);
        assert_eq!(a["liquid"]["rgba"][1], 0);
        // intensity=1 → 全碱式黄
        let b = transform(&[directive("color_change", 1.0, ph.clone())]);
        assert_eq!(b["liquid"]["rgba"][0], 255);
        assert_eq!(b["liquid"]["rgba"][1], 255);
        // intensity=0.5 → 中间橙（R=255, G=128 附近，容差四舍五入）
        let m = transform(&[directive("color_change", 0.5, ph)]);
        assert_eq!(m["liquid"]["rgba"][0], 255);
        let g = m["liquid"]["rgba"][1].as_u64().unwrap();
        assert!((120..=136).contains(&g), "G={} 应在 127.5 附近", g);
    }

    #[test]
    fn phenolphthalein_colorless_to_pink() {
        let ph = json!({"acid_color": "colorless", "base_color": "pink"});
        let low = transform(&[directive("color_change", 0.0, ph.clone())]);
        assert_eq!(low["liquid"]["rgba"][3], 0.0, "酸式无色应透明");
        let high = transform(&[directive("color_change", 1.0, ph)]);
        assert_eq!(high["liquid"]["rgba"][3], 1.0, "碱式粉红应不透明");
        let r = high["liquid"]["rgba"][0].as_u64().unwrap();
        assert_eq!(r, 255);
    }

    #[test]
    fn intensity_clamped() {
        let ph = json!({"acid_color": "red", "base_color": "yellow"});
        let mut d = directive("color_change", 99.0, ph);
        d["intensity"] = json!(99.0);
        let hi = transform(&[d]);
        assert_eq!(hi["liquid"]["rgba"][1], 255, "越界强度应夹到 1");
        let mut d2 = directive("color_change", -5.0, json!({"acid_color":"red","base_color":"yellow"}));
        d2["intensity"] = json!(-5.0);
        let lo = transform(&[d2]);
        assert_eq!(lo["liquid"]["rgba"][1], 0, "越界强度应夹到 0");
    }

    #[test]
    fn temperature_and_splash_effects() {
        let hot = transform(&[directive("temperature_change", 0.6,
            json!({"delta_K": 20.7, "temperature_K": 318.85}))]);
        let e = &hot["effects"][0];
        assert_eq!(e["type"], "temperature_change");
        assert_eq!(e["hot"], true);
        assert_eq!(e["delta_K"], 20.7);

        let splash = transform(&[directive("splash", 0.5, json!({"delta_T_K": 20.7}))]);
        assert_eq!(splash["effects"][0]["type"], "splash");
        assert_eq!(splash["effects"][0]["intensity"], 0.5);
    }

    #[test]
    fn malformed_directives_do_not_panic() {
        let bad = json!({"type": "color_change"}); // 缺 physics / intensity
        let out = transform(&[bad, json!("not-an-object"), json!({})]);
        assert!(out["visible"].as_array().unwrap().contains(&json!("color_change")));
        assert_eq!(out["liquid"]["rgba"][3], 0.0);
    }

    #[test]
    fn transform_json_accepts_bad_json() {
        let out: Value = serde_json::from_str(&transform_json("not json")).unwrap();
        assert_eq!(out["schema_version"], "st.appearance.v1");
        assert_eq!(out["effects"].as_array().unwrap().len(), 0);
    }
}
