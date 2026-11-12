import { useParams } from "react-router-dom";
import { SupplierRfqOffersView } from "@/features/fiyatlama";

export default function TekliflerPage() {
  const { id } = useParams<{ id?: string }>();
  return <SupplierRfqOffersView focusRfqId={id} />;
}
