          <a
            id="cb_email"
            class="btn"
            target="_blank"
            rel="noopener"
            title="Email"
            style="padding: 4px 8px"
            >✉️ Mail</a
          >
          <small id="cb_hint" style="opacity: 0.7; margin-left: 6px"></small>
        </div>
      </label>
      <label
        >Услуга
        <select
          id="qm_service"
          class="filter-select"
          required
          style="width: 100%"
        ></select>
        <small id="qm_service_hint" style="opacity: 0.7"></small>
      </label>

      <label
        >Кабинет
        <select
          id="qm_room"
          class="filter-select"
          required
          style="width: 100%"
        ></select>
      </label>

      <label
        >Начало
        <input
          type="datetime-local"
          id="qm_start"
          required
          step="300"
          style="width: 100%"
        />
      </label>

      <label
        >Окончание
        <input
          type="datetime-local"
          id="qm_end"
          step="300"
          style="width: 100%"
        />
      </label>

      <label
        >Статус
        <select
          id="qm_status"
          class="filter-select"
          required
          style="width: 100%"
        >
          <option value="scheduled">Запланирован</option>
          <option value="arrived">Прибыл</option>
          <option value="done">Завершён</option>
          <option value="cancelled">Отменён</option>
        </select>
      </label>

      <label style="grid-column: 1 / -1"
        >Комментарий
        <textarea id="qm_comment" rows="3" style="width: 100%"></textarea>
      </label>

      <div
        style="
          grid-column: 1/-1;
          display: flex;
          gap: 8px;
          align-items: center;
          margin-top: -4px;
        "
      >
        <button
          type="button"
          class="btn"
          id="btn_plus_15"
          style="
            border: 1px solid #dbeafd;
            border-radius: 8px;
            padding: 6px 10px;
