```html
{% extends "base.html" %} {% block content %}

<h2 style="margin: 8px 0 12px 0">РљР°СЂС‚РѕС‡РєР° РїР°С†РёРµРЅС‚Р°</h2>
<a href="/patients" class="btn" style="margin-bottom: 10px">в†©пёЋ Рљ СЃРїРёСЃРєСѓ</a>

<div
  style="
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 8px #e3eaf9b7;
    padding: 12px;
    max-width: 760px;
  "
>
  <form id="f" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px">
    <label style="grid-column: 1/-1"
      >Р¤РРћ
      <input
        type="text"
        id="full_name"
        class="filter-input"
        required
        style="width: 100%"
      />
    </label>

    <label
      >РўРµР»РµС„РѕРЅ
      <input
        type="tel"
        id="phone"
        class="filter-input"
        placeholder="+79991234567"
      />
    </label>

    <label
      >Р”Р°С‚Р° СЂРѕР¶РґРµРЅРёСЏ
      <input type="date" id="birth_date" class="filter-input" />
    </label>

    <label
      >в„– РєР°СЂС‚С‹
      <input
        type="number"
        id="card_no"
        class="filter-input"
        min="1"
        step="1"
        placeholder="Р°РІС‚Рѕ"
      />
    </label>

    <div
      style="
        grid-column: 1/-1;
        display: flex;
        gap: 8px;
        justify-content: flex-end;
        margin-top: 4px;
      "
    >
      <a href="/patients" class="btn">РћС‚РјРµРЅР°</a>
      <button type="submit" class="btn btn-primary">РЎРѕС…СЂР°РЅРёС‚СЊ</button>
    </div>
  </form>
</div>

{% endblock %} {% block scripts %}
<script>
  (function () {
    const pid = "{{ pid }}";
    const $ = (s) => document.querySelector(s);
    const f = $("#f");

    async function load() {
      try {
        const r = await fetch(`/api/patients/${pid}`);
        const data = await r.json();
        if (!data.ok) throw new Error(data.error || "error");
        const it = data.item;
        $("#full_name").value = it.full_name || "";
        $("#phone").value = it.phone || "";
        $("#birth_date").value = (it.birthdate || "").toString().slice(0, 10);
        $("#card_no").value = it.card_no ?? "";
      } catch (e) {
        alert("РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ РєР°СЂС‚РѕС‡РєСѓ");
        location.href = "/patients";
      }
    }

    f.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const payload = {
        full_name: $("#full_name").value.trim(),
        phone: $("#phone").value.trim(),
        birth_date: $("#birth_date").value || "",
        card_no:
          $("#card_no").value === "" ? null : Number($("#card_no").value),
      };
      try {
        const r = await fetch(`/api/patients/${pid}/update`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (!r.ok || !data.ok) {
          alert(data.error || "РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ");
          return;
        }
        alert("РЎРѕС…СЂР°РЅРµРЅРѕ");
        location.href = "/patients";
      } catch {
        alert("РЎРµС‚СЊ РЅРµРґРѕСЃС‚СѓРїРЅР°");
      }
    });

    load();
  })();
</script>
{% endblock %}

```
