import { useState } from 'react'

type StarRatingProps = {
  name: string
  value: number
  onChange: (rating: number) => void
  disabled: boolean
}

export default function StarRating({ name, value, onChange, disabled }: StarRatingProps) {
  const [hoveredRating, setHoveredRating] = useState(0)
  const preview = hoveredRating || value

  return (
    <fieldset className="star-rating" disabled={disabled}>
      <legend>Rate this book to return it</legend>
      <div className="star-rating-stars">
        {[1, 2, 3, 4, 5].map((rating) => (
          <label
            key={rating}
            className="star-rating-option"
            onMouseEnter={() => !disabled && setHoveredRating(rating)}
            onMouseLeave={() => setHoveredRating(0)}
          >
            <input
              type="radio"
              name={name}
              value={rating}
              checked={value === rating}
              onChange={() => onChange(rating)}
              aria-label={`${rating} ${rating === 1 ? 'star' : 'stars'}`}
            />
            <span className={rating <= preview ? 'star-filled' : ''} aria-hidden="true">
              ★
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}
