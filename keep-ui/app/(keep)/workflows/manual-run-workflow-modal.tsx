import { Button, Select, SelectItem, Text } from "@tremor/react";

import Modal from "@/components/ui/Modal";
import { useWorkflows } from "utils/hooks/useWorkflows";
import { useState } from "react";
import { toast } from "react-toastify";
import { useRouter } from "next/navigation";
import { IncidentDto } from "@/entities/incidents/model";
import { AlertDto } from "@/entities/alerts/model";
import { useApi } from "@/shared/lib/hooks/useApi";
import { showErrorToast } from "@/shared/ui";

interface Props {
  alert?: AlertDto | null | undefined;
  incident?: IncidentDto | null | undefined;
  handleClose: () => void;
}

export default function ManualRunWorkflowModal({
  alert,
  incident,
  handleClose,
}: Props) {
  /**
   *
   */
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<
    string | undefined
  >(undefined);
  const { data: workflows } = useWorkflows({});
  const api = useApi();
  const router = useRouter();

  const isOpen = !!alert || !!incident;

  const clearAndClose = () => {
    setSelectedWorkflowId(undefined);
    handleClose();
  };

  const handleRun = async () => {
    try {
      const responseData = await api.post(
        `/workflows/${selectedWorkflowId}/run`,
        {
          type: alert ? "alert" : "incident",
          body: alert ? alert : incident,
        }
      );

      const { workflow_execution_id } = responseData;
      const executionUrl = `/workflows/${selectedWorkflowId}/runs/${workflow_execution_id}`;

      toast.success(
        <div>
          Workflow started successfully.{" "}
          <a
            href={executionUrl}
            className="text-orange-500 hover:text-orange-600 underline"
            onClick={(e) => {
              e.preventDefault();
              router.push(executionUrl);
            }}
          >
            View execution
          </a>
        </div>,
        { position: "top-right" }
      );
    } catch (error) {
      showErrorToast(error, "Failed to start workflow");
    }
    clearAndClose();
  };

  return (
    <Modal
      onClose={clearAndClose}
      isOpen={isOpen}
      className="overflow-visible"
      beforeTitle={alert?.name}
      title="Run Workflow"
    >
      <Text className="mb-1 mt-4">Select workflow to run</Text>
      {workflows ? (
        <Select
          value={selectedWorkflowId}
          onValueChange={setSelectedWorkflowId}
        >
          {workflows
            .filter((workflow) => !workflow.disabled)
            .map((workflow) => {
              return (
                <SelectItem key={workflow.id} value={workflow.id}>
                  {workflow.description}
                </SelectItem>
              );
            })}
        </Select>
      ) : (
        <div>No workflows found</div>
      )}
      <div className="flex justify-end gap-2 mt-4">
        <Button onClick={clearAndClose} color="orange" variant="secondary">
          Cancel
        </Button>
        <Button
          onClick={handleRun}
          color="orange"
          disabled={!selectedWorkflowId}
        >
          Run
        </Button>
      </div>
    </Modal>
  );
}
