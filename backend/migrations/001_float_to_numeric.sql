-- Migration: Convert Float columns to Numeric for precision
-- Date: 2025-12-31
-- Description: Changes all Float columns to Numeric(20, 8) for exact financial calculations

-- ============================================================================
-- SIGNAL_MESSAGES TABLE
-- ============================================================================

ALTER TABLE signal_messages
ALTER COLUMN entry TYPE NUMERIC(20, 8);

ALTER TABLE signal_messages
ALTER COLUMN stop_loss TYPE NUMERIC(20, 8);

ALTER TABLE signal_messages
ALTER COLUMN take_profit TYPE NUMERIC(20, 8);

-- ============================================================================
-- TRADES TABLE
-- ============================================================================

ALTER TABLE trades
ALTER COLUMN entry_price TYPE NUMERIC(20, 8);

ALTER TABLE trades
ALTER COLUMN entry_quantity TYPE NUMERIC(20, 8);

ALTER TABLE trades
ALTER COLUMN stop_loss TYPE NUMERIC(20, 8);

ALTER TABLE trades
ALTER COLUMN take_profit TYPE NUMERIC(20, 8);

ALTER TABLE trades
ALTER COLUMN tp TYPE NUMERIC(20, 8);

ALTER TABLE trades
ALTER COLUMN exit_price TYPE NUMERIC(20, 8);

ALTER TABLE trades
ALTER COLUMN pnl TYPE NUMERIC(20, 8);

ALTER TABLE trades
ALTER COLUMN pnl_percent TYPE NUMERIC(10, 4);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Run this query to verify all columns were updated:
SELECT
    table_name,
    column_name,
    data_type,
    numeric_precision,
    numeric_scale
FROM
    information_schema.columns
WHERE
    table_name IN ('signal_messages', 'trades')
    AND column_name IN ('entry', 'stop_loss', 'take_profit', 'entry_price',
                        'entry_quantity', 'tp', 'exit_price', 'pnl', 'pnl_percent')
ORDER BY
    table_name, column_name;
