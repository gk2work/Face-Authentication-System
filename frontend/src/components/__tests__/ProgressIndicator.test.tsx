import { describe, it, expect } from 'vitest';
import { render, screen } from '../../test/utils';
import { ProgressIndicator } from '../ProgressIndicator';

describe('ProgressIndicator', () => {
  it('renders progress bar with correct value', () => {
    const { container } = render(<ProgressIndicator progress={50} />);
    const progressBar = container.querySelector('.MuiLinearProgress-bar');
    expect(progressBar).toBeInTheDocument();
  });

  it('displays percentage by default', () => {
    render(<ProgressIndicator progress={75} />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('hides percentage when showPercentage is false', () => {
    render(<ProgressIndicator progress={75} showPercentage={false} />);
    expect(screen.queryByText('75%')).not.toBeInTheDocument();
  });

  it('displays custom message', () => {
    render(<ProgressIndicator progress={50} message="Uploading file..." />);
    expect(screen.getByText('Uploading file...')).toBeInTheDocument();
  });

  it('rounds progress percentage', () => {
    render(<ProgressIndicator progress={33.7} />);
    expect(screen.getByText('34%')).toBeInTheDocument();
  });

  it('handles 0% progress', () => {
    render(<ProgressIndicator progress={0} />);
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('handles 100% progress', () => {
    render(<ProgressIndicator progress={100} />);
    expect(screen.getByText('100%')).toBeInTheDocument();
  });
});
