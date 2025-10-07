    window.__DICT_CACHE__ = window.__DICT_CACHE__ || null;

    // Универсальная заливка options
    function fillOptions(selectEl, items, selectedId = "") {
      if (!selectEl) return;
      const toId = (x) => x._id ?? x.id ?? "";
      const toName = (x) => x.full_name ?? x.name ?? "";
      const html = (items || [])
        .map((x) => {
          const id = toId(x),
            name = toName(x);
          return `<option value="${id}">${name}</option>`;
        })
        .join("");
      selectEl.innerHTML = html;
      if (selectedId) selectEl.value = selectedId;
      if (!selectEl.value || selectEl.value === "undefined") {
        const first = selectEl.querySelector("option")?.value || "";
        selectEl.value = first;
      }
    }

    // Загрузка словарей (нормализация)
    async function loadDictsOnce() {
      if (window.__DICT_CACHE__) return window.__DICT_CACHE__;
      const r = await fetch("/api/dicts");
      const raw = await r.json();
      if (!raw?.ok) throw new Error("dicts load failed");

      const norm = (arr) =>
        (arr || []).map((x) => ({
          id: x._id ?? x.id ?? "",
          name: x.full_name ?? x.name ?? "",
          duration_min: x.duration_min,
        }));
      const data = {
        ok: true,
        doctors: norm(raw.doctors),
        patients: norm(raw.patients),
        rooms: norm(raw.rooms),
        services: norm(raw.services).map((s) => ({
          ...s,
          duration_min: s.duration_min ?? 30,
        })),
      };
      window.__DICT_CACHE__ = data;
      return data;
    }

    // ---------- элементы модалки ----------
    const qm = {
      modal: $("#quickModal"),
      close: $("#qmClose"),
      form: $("#qmForm"),
      id: $("#qm_id"),
      doctor: $("#qm_doctor"),
      patient: $("#qm_patient"),
      service: $("#qm_service"),
      serviceHint: $("#qm_service_hint"),
      room: $("#qm_room"),
      start: $("#qm_start"),
      end: $("#qm_end"),
      status: $("#qm_status"),
      comment: $("#qm_comment"),
      warn: $("#qm_warn"),
      btnDel: $("#qmDelete"),
      btnPlus15: document.querySelector("#quickModal #btn_plus_15"),
      btnPlus30: document.querySelector("#quickModal #btn_plus_30"),
      btnPlus60: document.querySelector("#quickModal #btn_plus_60"),
      btnTomorrow: document.querySelector("#quickModal #btn_move_tomorrow"),
      btnFirstFree: document.querySelector("#quickModal #btn_first_free"),

      // блок «Новый пациент»
      patientAddBtn: document.getElementById("qm_patient_add"),
      patientNewRow: document.getElementById("qm_patient_new"),
      newFullName: document.getElementById("qm_new_full_name"),
      newPhone: document.getElementById("qm_new_phone"),
      newBirth: document.getElementById("qm_new_birth"),
      patientSaveBtn: document.getElementById("qm_patient_save"),
      patientCancelBtn: document.getElementById("qm_patient_cancel"),
    };

    function hideNewPatientRow() {
      if (!qm) return;
      if (qm.patientNewRow) qm.patientNewRow.style.display = "none";
      if (qm.newFullName) qm.newFullName.value = "";
      if (qm.newPhone) qm.newPhone.value = "";
      if (qm.newBirth) qm.newBirth.value = "";
    }

    // --- contacts bar (Tel/WA/TG/Max/Mail) ---------------------------------
