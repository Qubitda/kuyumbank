import { DomainPlaceholder } from "@/components/route-states";

export default function Page() {
  return (
    <DomainPlaceholder
      title="Sipariş"
      backendApp="siparis"
      note="Cart → checkout → order + RFQ."
    />
  );
}
