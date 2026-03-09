import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { ToothIcon } from "@/components/icons/tooth-icon";
import { APP_CONFIG } from "@/lib/constants";

interface AboutDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AboutDialog({ open, onOpenChange }: AboutDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ToothIcon className="h-5 w-5" />
            Giới thiệu về {APP_CONFIG.NAME}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {APP_CONFIG.DESCRIPTION}
          </p>
          <Separator />
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">Đội ngũ phát triển</h4>
            <div className="space-y-1 text-sm text-muted-foreground">
              <p>
                <span className="font-medium text-foreground">
                  Developer:
                </span>{" "}
                {APP_CONFIG.DEVELOPER}
              </p>
              <p>
                <span className="font-medium text-foreground">Version:</span>{" "}
                {APP_CONFIG.VERSION}
              </p>
              <p>
                <span className="font-medium text-foreground">
                  Công nghệ:
                </span>{" "}
                {APP_CONFIG.TECH_STACK}
              </p>
            </div>
          </div>
          <Separator />
          <p className="text-xs text-muted-foreground">
            © 2026 {APP_CONFIG.NAME}. Thông tin chỉ mang tính tham khảo,
            không thay thế tư vấn trực tiếp từ bác sĩ nha khoa.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
