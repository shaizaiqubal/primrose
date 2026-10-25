import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'

type ButtonVariant = 'primary' | 'ghost' | 'icon'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
}

export function Button({ className = '', variant = 'ghost', ...props }: ButtonProps) {
  return <button className={`button button--${variant} ${className}`.trim()} {...props} />
}

type ChipProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  selected?: boolean
}

export function Chip({ className = '', selected = false, ...props }: ChipProps) {
  return (
    <button
      aria-pressed={selected}
      className={`chip${selected ? ' chip--selected' : ''} ${className}`.trim()}
      {...props}
    />
  )
}

type CardProps = {
  children: ReactNode
  className?: string
  as?: 'article' | 'section' | 'div'
}

export function Card({ as: Tag = 'article', children, className = '' }: CardProps) {
  return <Tag className={`card ${className}`.trim()}>{children}</Tag>
}

type FieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  requirement?: 'Required' | 'Optional'
}

export function Field({ id, label, requirement, className = '', ...props }: FieldProps) {
  const inputId = id ?? props.name ?? label.toLowerCase().replaceAll(' ', '-')

  return (
    <div className="field">
      <label className="field__label" htmlFor={inputId}>
        {label}
        {requirement && <span className="field__requirement">{requirement}</span>}
      </label>
      <input id={inputId} className={`field__input ${className}`.trim()} {...props} />
    </div>
  )
}

type HeaderProps = {
  authenticated?: boolean
  activePath?: string
}

export function Header({ authenticated = false, activePath }: HeaderProps) {
  const currentPath = useLocation().pathname
  const selectedPath = activePath ?? currentPath
  const authRoute = ['/signin', '/signup', '/inbox', '/verify-email', '/unauthorized'].includes(currentPath)
  const showNavigation = authenticated || !authRoute
  const links = authenticated
    ? [
        { label: 'Topics', href: '/topics' },
        { label: 'Entities', href: '/entities' },
        { label: 'Library', href: '/library' },
      ]
    : [
        { label: 'Topics', href: '/topics' },
        { label: 'Entities', href: '/entities' },
        { label: 'Login', href: '/signin' },
      ]

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <NavLink className="wordmark" to="/" aria-label="Primrose home">
          <span className="wordmark__ring" aria-hidden="true" />
          <span>Primrose</span>
        </NavLink>
        {showNavigation && (
          <nav className="site-nav" aria-label="Main navigation">
            {links.map(({ label, href }) => (
              <Link
                key={href}
                aria-current={selectedPath === href ? 'page' : undefined}
                className={`site-nav__link${selectedPath === href ? ' is-active' : ''}`}
                to={href}
              >
                {label}
              </Link>
            ))}
          </nav>
        )}
      </div>
    </header>
  )
}