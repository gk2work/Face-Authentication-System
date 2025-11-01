import { describe, it, expect } from 'vitest';
import { render, screen } from '../../test/utils';
import { LoadingSpinner } from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with default message', () => {
    render(<LoadingSpinner />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<LoadingSpinner message="Please wait..." />);
    expect(screen.getByText('Please wait...')).toBeInTheDocument();
  });

  it('renders without message when message is empty', () => {
    render(<LoadingSpinner message="" />);
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });

  it('renders as full screen when fullScreen prop is true', () => {
    const { container } = render(<LoadingSpinner fullScreen />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveStyle({ minHeight: '100vh' });
  });

  it('renders CircularProgress component', () => {
    const { container } = render(<LoadingSpinner />);
    const progress = container.querySelector('.MuiCircularProgress-root');
    expect(progress).toBeInTheDocument();
  });
});
