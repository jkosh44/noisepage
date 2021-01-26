#pragma once

#include <array>

#include "catalog/catalog_column_def.h"
#include "catalog/catalog_defs.h"
#include "parser/expression_defs.h"

namespace noisepage::storage {
class RecoveryManager;
}  // namespace noisepage::storage

namespace noisepage::execution::compiler {
class AnalyzeTranslator;
}  // namespace noisepage::execution::compiler

namespace noisepage::catalog::postgres {
class Builder;
class PgStatisticImpl;

/** The OIDs used by the NoisePage version of pg_statistic. */
class PgStatistic {
 private:
  friend class execution::compiler::AnalyzeTranslator;
  friend class storage::RecoveryManager;
  friend class Builder;
  friend class PgStatisticImpl;

  static constexpr table_oid_t STATISTIC_TABLE_OID = table_oid_t(91);
  static constexpr index_oid_t STATISTIC_OID_INDEX_OID = index_oid_t(92);

  /*
   * Column names of the form "STA[name]" are present in the PostgreSQL
   * catalog specification and columns of the form "STA_[name]" are
   * noisepage-specific additions.
   */
  static constexpr CatalogColumnDef<table_oid_t, uint32_t> STARELID{col_oid_t{1}};
  static constexpr CatalogColumnDef<col_oid_t, uint32_t> STAATTNUM{col_oid_t{2}};
  static constexpr CatalogColumnDef<uint32_t, uint32_t> STA_NUMROWS{col_oid_t{3}};
  static constexpr CatalogColumnDef<uint32_t, uint32_t> STA_NONNULLROWS{col_oid_t{4}};
  static constexpr CatalogColumnDef<uint32_t, uint32_t> STA_DISTINCTROWS{col_oid_t{5}};
  static constexpr CatalogColumnDef<storage::VarlenEntry> STA_TOPK{col_oid_t{6}};
  static constexpr CatalogColumnDef<storage::VarlenEntry> STA_HISTOGRAM{col_oid_t{7}};

  static constexpr uint8_t NUM_PG_STATISTIC_COLS = 7;

  static constexpr std::array<col_oid_t, NUM_PG_STATISTIC_COLS> PG_STATISTIC_ALL_COL_OIDS = {
      STARELID.oid_,         STAATTNUM.oid_, STA_NUMROWS.oid_,  STA_NONNULLROWS.oid_,
      STA_DISTINCTROWS.oid_, STA_TOPK.oid_,  STA_HISTOGRAM.oid_};

 public:
  /**
   * Contains information on how to derive values for the columns within pg_statistic
   */
  struct PgStatisticColInfo {
    /** The type of aggregate to use */
    parser::ExpressionType aggregate_type_;
    /** Whether the aggregate is distinct */
    bool distinct_;
    /** Oid of the column */
    catalog::col_oid_t column_oid_;
    /** Human readable name of the column */
    std::string_view name_;
  };
  /** Number of aggregates per column that Analyze uses */
  static constexpr uint8_t NUM_ANALYZE_AGGREGATES = 4;
  /** Information on each aggregate that Analyze uses to compute statistics */
  static constexpr std::array<PgStatisticColInfo, NUM_ANALYZE_AGGREGATES> ANALYZE_AGGREGATES = {
      {// COUNT(col) - non-null rows
       {parser::ExpressionType::AGGREGATE_COUNT, false, STA_NONNULLROWS.oid_, "non_null_row"},
       // COUNT(DISTINCT col) - distinct values
       {parser::ExpressionType::AGGREGATE_COUNT, true, STA_DISTINCTROWS.oid_, "distinct_row"},
       // TOPK(col)
       {parser::ExpressionType::AGGREGATE_TOP_K, false, STA_TOPK.oid_, "top_k"},
       // HISTOGRAM(col)
       {parser::ExpressionType::AGGREGATE_HISTOGRAM, false, STA_HISTOGRAM.oid_, "histogram"}}};
};

}  // namespace noisepage::catalog::postgres
