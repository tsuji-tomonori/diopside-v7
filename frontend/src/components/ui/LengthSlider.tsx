import { ChangeEvent, CSSProperties } from 'react';

type RangeValue = {
  min: number;
  max: number;
};

const formatLength = (value: number, upper = false) => {
  if (value >= 300 && upper) {
    return '上限なし';
  }

  return `${Math.floor(value / 60)}h${value % 60 ? `${value % 60}m` : ''}`;
};

export function LengthSlider({
  min,
  max,
  onChange,
}: {
  min: number;
  max: number;
  onChange: (range: RangeValue) => void;
}) {
  const update = (key: keyof RangeValue) => (event: ChangeEvent<HTMLInputElement>) => {
    const value = Number(event.target.value);
    const nextRange = key === 'min'
      ? { min: Math.min(value, max), max }
      : { min, max: Math.max(value, min) };

    onChange(nextRange);
  };

  const rangeStyle = {
    '--range-start': `${(min / 300) * 100}%`,
    '--range-end': `${(max / 300) * 100}%`,
  } as CSSProperties;

  return (
    <div className="dio-length-slider">
      <output>
        {formatLength(min)}〜{formatLength(max, true)}
      </output>
      <div className="dio-length-slider__inputs" style={rangeStyle}>
        <input
          aria-label="長さの下限"
          aria-valuetext={formatLength(min)}
          className="dio-length-slider__thumb dio-length-slider__thumb--min"
          max="300"
          min="0"
          onChange={update('min')}
          step="15"
          type="range"
          value={min}
        />
        <input
          aria-label="長さの上限"
          aria-valuetext={formatLength(max, true)}
          className="dio-length-slider__thumb dio-length-slider__thumb--max"
          max="300"
          min="0"
          onChange={update('max')}
          step="15"
          type="range"
          value={max}
        />
      </div>
      <div className="dio-caption">0　1h　2h　3h　4h　5h+</div>
    </div>
  );
}
