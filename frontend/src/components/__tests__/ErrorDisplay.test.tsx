import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../test/utils';
import userEvent from '@testing-library/user-event';
import { ErrorDisplay } from '../ErrorDisplay';

describe('ErrorDisplay', () => {
  it('renders error message from string', () => {
    render(<ErrorDisplay error="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('renders error message from Error object', () => {
    const error = new Error('Test error message');
    render(<ErrorDisplay error={error} />);
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('renders custom title', () => {
    render(<ErrorDisplay error="Error" title="Custom Error Title" />);
    expect(screen.getByText('Custom Error Title')).toBeInTheDocument();
  });

  it('renders retry button when onRetry is provided', () => {
    const onRetry = vi.fn();
    render(<ErrorDisplay error="Error" onRetry={onRetry} />);
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('does not render retry button when onRetry is not provided', () => {
    render(<ErrorDisplay error="Error" />);
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(<ErrorDisplay error="Error" onRetry={onRetry} />);
    
    const retryButton = screen.getByRole('button', { name: /retry/i });
    await user.click(retryButton);
    
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders with different severity levels', () => {
    const { rerender } = render(<ErrorDisplay error="Error" severity="error" />);
    expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardError');

    rerender(<ErrorDisplay error="Warning" severity="warning" />);
    expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardWarning');

    rerender(<ErrorDisplay error="Info" severity="info" />);
    expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardInfo');
  });
});
