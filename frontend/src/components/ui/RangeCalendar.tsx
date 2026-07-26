import { KeyboardEvent, useMemo, useState } from 'react';

import { Icon } from './Icon';

type DateRange = {
  from?: string;
  to?: string;
};

const dateKey = (date: Date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}-${month}-${day}`;
};

const fromKey = (value: string) => new Date(`${value}T00:00:00`);

const addDays = (value: string, amount: number) => {
  const date = fromKey(value);
  date.setDate(date.getDate() + amount);

  return dateKey(date);
};

const addMonths = (value: string, amount: number) => {
  const date = fromKey(value);
  date.setMonth(date.getMonth() + amount);

  return dateKey(date);
};

export function RangeCalendar({
  from,
  to,
  onChange,
  onBack,
  streamedDates = [],
}: {
  from?: string;
  to?: string;
  onChange: (range: DateRange) => void;
  onBack?: () => void;
  streamedDates?: string[];
}) {
  const initialDate = from ? fromKey(from) : new Date();
  const [month, setMonth] = useState(
    () => new Date(initialDate.getFullYear(), initialDate.getMonth(), 1),
  );
  const [activeDate, setActiveDate] = useState(from ?? dateKey(new Date()));
  const today = dateKey(new Date());

  const weeks = useMemo(() => {
    const first = new Date(month.getFullYear(), month.getMonth(), 1);
    const lastDay = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
    const cells: Array<Date | null> = Array.from({ length: 42 }, (_, index) => {
      const day = index - first.getDay() + 1;

      return day > 0 && day <= lastDay
        ? new Date(month.getFullYear(), month.getMonth(), day)
        : null;
    });

    return Array.from({ length: 6 }, (_, index) => cells.slice(index * 7, index * 7 + 7));
  }, [month]);

  const choose = (key: string) => {
    if (!from || to) {
      onChange({ from: key });
      return;
    }

    onChange(key < from ? { from: key, to: from } : { from, to: key });
  };

  const moveFocus = (nextKey: string) => {
    if (nextKey > today) {
      return;
    }

    const nextDate = fromKey(nextKey);
    setActiveDate(nextKey);
    setMonth(new Date(nextDate.getFullYear(), nextDate.getMonth(), 1));
    window.setTimeout(() => {
      document.querySelector<HTMLButtonElement>(`[data-date="${nextKey}"]`)?.focus();
    }, 0);
  };

  const handleDateKeyDown = (event: KeyboardEvent<HTMLButtonElement>, key: string) => {
    let nextKey: string | undefined;

    switch (event.key) {
      case 'ArrowLeft':
        nextKey = addDays(key, -1);
        break;
      case 'ArrowRight':
        nextKey = addDays(key, 1);
        break;
      case 'ArrowUp':
        nextKey = addDays(key, -7);
        break;
      case 'ArrowDown':
        nextKey = addDays(key, 7);
        break;
      case 'Home':
        nextKey = addDays(key, -fromKey(key).getDay());
        break;
      case 'End':
        nextKey = addDays(key, 6 - fromKey(key).getDay());
        break;
      case 'PageUp':
        nextKey = addMonths(key, event.shiftKey ? -12 : -1);
        break;
      case 'PageDown':
        nextKey = addMonths(key, event.shiftKey ? 12 : 1);
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        choose(key);
        return;
      case 'Escape':
        event.currentTarget.blur();
        return;
      default:
        return;
    }

    event.preventDefault();
    moveFocus(nextKey);
  };

  return (
    <section aria-label="投稿日" className="dio-calendar">
      <h3 className="sr-only">投稿日</h3>
      <header>
        {onBack ? <button className="dio-calendar__back" onClick={onBack} type="button">条件に戻る</button> : null}
        <button
          aria-label="前の月"
          onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() - 1, 1))}
          type="button"
        >
          <Icon name="chevron_left" size={20} />
        </button>
        <strong className="dio-calendar__month">{month.getFullYear()}年{month.getMonth() + 1}月</strong>
        <button
          aria-label="次の月"
          onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() + 1, 1))}
          type="button"
        >
          <Icon name="chevron_right" size={20} />
        </button>
        <button className="dio-calendar__clear" onClick={() => onChange({})} type="button">
          クリア
        </button>
      </header>
      <div aria-hidden="true" className="dio-calendar__week">
        {'日月火水木金土'.split('').map((day) => (
          <span key={day}>{day}</span>
        ))}
      </div>
      <div aria-label="投稿日カレンダー" className="dio-calendar__grid" role="grid">
        {weeks.map((week, weekIndex) => (
          <div className="dio-calendar__row" key={`week-${weekIndex}`} role="row">
            {week.map((date, dayIndex) => {
              if (!date) {
                return <span aria-hidden="true" key={`blank-${dayIndex}`} role="presentation" />;
              }

              const key = dateKey(date);
              const disabled = key > today;
              const selected = key === from || key === to;
              const inRange = Boolean(from && to && key > from && key < to);

              return (
                <button
                  aria-selected={selected}
                  className={`${inRange ? 'is-in-range' : ''} ${selected ? 'is-selected' : ''}`}
                  data-date={key}
                  disabled={disabled}
                  key={key}
                  onClick={() => choose(key)}
                  onFocus={() => setActiveDate(key)}
                  onKeyDown={(event) => handleDateKeyDown(event, key)}
                  role="gridcell"
                  tabIndex={key === activeDate ? 0 : -1}
                  type="button"
                >
                  <time dateTime={key}>{date.getDate()}</time>
                  {streamedDates.includes(key) ? <i aria-label="配信あり" /> : null}
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </section>
  );
}
