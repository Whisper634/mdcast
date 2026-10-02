// B站 API 实操笔记（2026-09-30 验证通过）
// 在已登录 bilibili.com 的标签页控制台/桥接 evaluate 中运行。
// 依赖：cookie 中有 bili_jct（CSRF）。

// === 1. WBI 签名（新版接口必需；旧版 vc 接口不需要）===
const MIXIN_KEY_ENC_TAB=[46,47,18,2,53,8,23,32,15,50,10,31,58,3,45,35,27,43,5,20,11,42,57,30,25,49,28,13,56,41,19,24,55,44,12,22,52,39,36,34,6,7,48,17,38,51,40,1,33,54,26,37,29,9,4,14,16,20,57,53,54,17,38,44,10,62,39,61,7,60,31,56,40];
async function getMixin(){
  const nav=await (await fetch("https://api.bilibili.com/x/web-interface/nav",{credentials:"include"})).json();
  const iu=nav.data.wbi_img.img_url, su=nav.data.wbi_img.sub_url;
  const ik=iu.slice(iu.lastIndexOf("/")+1,iu.lastIndexOf("."));
  const sk=su.slice(su.lastIndexOf("/")+1,su.lastIndexOf("."));
  const raw=ik+sk;
  let m=""; for(let i=0;i<32;i++) m+=raw[MIXIN_KEY_ENC_TAB[i]];
  return m;
}
async function md5(s){
  const buf=await crypto.subtle.digest("MD5",new TextEncoder().encode(s));
  return Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,"0")).join("");
}
async function wbiSign(params){
  const mixin=await getMixin();
  params.wts=Math.floor(Date.now()/1000);
  const keys=Object.keys(params).sort();
  const q=keys.map(k=>k+"="+encodeURIComponent(String(params[k])).replace(/[!'()*]/g,"")).join("&");
  return q+"&w_rid="+(await md5(q+mixin));
}
// 验证签名：x/web-interface/wbi/search/default?web_location=333.33 返回 code 0 即正确。

// === 2. 修改签名（返回 code 0，但显示有审核延迟/可能静默拒绝，需复查）===
// POST https://api.bilibili.com/x/member/web/sign/update?csrf=<bili_jct>
//   Content-Type: application/x-www-form-urlencoded
//   body: sign=<urlencoded>

// === 3. 发文字动态（旧版接口，今晚实测通过 ✅）===
// POST https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/create?csrf=<bili_jct>
//   Content-Type: application/x-www-form-urlencoded
//   body 字段: dynamic_id=0, type=4, rid=0, content=<文本>, extension={}
// 成功返回 data.dynamic_id_str。注意：实际落库类型可能显示为 DRAW，不影响可见性。
// 删除动态：POST https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/rm_dynamic?csrf=<bili_jct>
//   body: dynamic_id=<id>

// === 4. 新版 create/dyn 接口（未走通）===
// POST https://api.bilibili.com/x/dynamic/feed/create/dyn + wbi 签名
// 两种 content-type 均报 400/4100001，疑似需要 x-bili-aurora-eid 等设备头（WASM 生成）。
// 发布自动化若要做，建议走 Playwright 驱动官方页面而不是硬凑 API。

// === 5. 修改昵称 ===
// 需 6 个硬币/次（POST x/member/web/uname/update），新号硬币不足时先每日登录攒币。
