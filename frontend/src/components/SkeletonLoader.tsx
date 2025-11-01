import { Box, Skeleton, Paper } from '@mui/material';

interface SkeletonLoaderProps {
  variant?: 'card' | 'table' | 'list' | 'detail';
  count?: number;
}

export const SkeletonLoader = ({ variant = 'card', count = 1 }: SkeletonLoaderProps) => {
  const renderCardSkeleton = () => (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Skeleton variant="text" width="60%" height={32} />
      <Skeleton variant="text" width="40%" />
      <Skeleton variant="rectangular" height={100} sx={{ mt: 2 }} />
    </Paper>
  );

  const renderTableSkeleton = () => (
    <Box>
      <Skeleton variant="rectangular" height={56} sx={{ mb: 1 }} />
      {Array.from({ length: count }).map((_, index) => (
        <Skeleton key={index} variant="rectangular" height={52} sx={{ mb: 1 }} />
      ))}
    </Box>
  );

  const renderListSkeleton = () => (
    <Box>
      {Array.from({ length: count }).map((_, index) => (
        <Box key={index} sx={{ mb: 2 }}>
          <Skeleton variant="text" width="80%" height={24} />
          <Skeleton variant="text" width="60%" />
        </Box>
      ))}
    </Box>
  );

  const renderDetailSkeleton = () => (
    <Box>
      <Skeleton variant="rectangular" height={200} sx={{ mb: 2 }} />
      <Skeleton variant="text" width="40%" height={40} sx={{ mb: 2 }} />
      <Skeleton variant="text" width="100%" />
      <Skeleton variant="text" width="100%" />
      <Skeleton variant="text" width="80%" />
      <Box sx={{ mt: 3 }}>
        <Skeleton variant="text" width="30%" height={32} sx={{ mb: 1 }} />
        <Skeleton variant="rectangular" height={150} />
      </Box>
    </Box>
  );

  switch (variant) {
    case 'card':
      return <>{Array.from({ length: count }).map((_, i) => <Box key={i}>{renderCardSkeleton()}</Box>)}</>;
    case 'table':
      return renderTableSkeleton();
    case 'list':
      return renderListSkeleton();
    case 'detail':
      return renderDetailSkeleton();
    default:
      return renderCardSkeleton();
  }
};
