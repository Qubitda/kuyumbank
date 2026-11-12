/** OpenAPI SupplierStock */
export interface StockBalance {
  varyant_id: number;
  birim: string;
  available: string;
  on_hand?: string;
  reserved?: string;
  blocked?: string;
  teklif_id?: number;
  warehouse_id?: number;
}

export interface StockAdjustmentRequest {
  warehouse_id: number;
  teklif_id: number;
  miktar: string;
  neden?: string;
}
