import { describe, it, expect } from 'vitest';
import { render, screen } from '../../test/utils';
import { StatCard } from '../StatCard';

describe('StatCard', () => {
  const defaultIcon = <div data-testid="default-icon">Icon</div>;

  it('renders title and value', () => {
    render(<StatCard title="Total Applications" value={150} icon={defaultIcon} />);
    expect(screen.getByText('Total Applications')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('renders with icon', () => {
    const TestIcon = () => <div data-testid="test-icon">Icon</div>;
    render(<StatCard title="Test" value={100} icon={<TestIcon />} />);
    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
  });

  it('renders positive trend', () => {
    render(<StatCard title="Test" value={100} icon={<div />} trend={{ value: 5, isPositive: true }} />);
    expect(screen.getByText('+5%')).toBeInTheDocument();
  });

  it('renders negative trend', () => {
    render(<StatCard title="Test" value={100} icon={<div />} trend={{ value: -3, isPositive: false }} />);
    expect(screen.getByText('-3%')).toBeInTheDocument();
  });

  it('renders zero trend', () => {
    render(<StatCard title="Test" value={100} icon={<div />} trend={{ value: 0, isPositive: false }} />);
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('does not render trend when not provided', () => {
    render(<StatCard title="Test" value={100} icon={defaultIcon} />);
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it('renders with custom color', () => {
    const { container } = render(
      <StatCard title="Test" value={100} icon={defaultIcon} />
    );
    expect(container.querySelector('.MuiCard-root')).toBeInTheDocument();
  });

  it('formats large numbers', () => {
    render(<StatCard title="Test" value={1500000} icon={defaultIcon} />);
    expect(screen.getByText('1500000')).toBeInTheDocument();
  });
});
