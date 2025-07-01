import { Link } from "react-router-dom";
import { useInstances } from "../hooks/useInstances";

export default function Instances() {
    const { data, isLoading, isError } = useInstances();

    return (
        <div className="px-4 sm:px-[10%] py-6 flex flex-col gap-4 w-full">
            {isLoading && <p>Loading servers…</p>}
            {isError   && <p className="text-red-600">Failed to load instances.</p>}

            {data?.map(inst => (
                <div
                    key={inst.name}
                    className="flex justify-between items-center gap-4 rounded-xl shadow p-4 bg-gray-800 text-white"
                >
                    <h2 className="font-semibold text-lg">{inst.name}</h2>

                    <div className="flex items-center gap-4">
                        <p className="uppercase">
                            Status:&nbsp;
                            <span
                                className={
                                    inst.status === "running"
                                        ? "text-green-400"
                                        : inst.status === "stopped"
                                        ? "text-yellow-400"
                                        : "text-gray-400"
                                }
                            >
                                {inst.status}
                            </span>
                        </p>

                        <Link
                            to={`/instances/${inst.name}`}
                            className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                            View
                        </Link>
                    </div>
                </div>
            ))}

            {/* Create new instance row */}
            <div className="mt-2">
                <Link
                    to="/instances/create"
                    className="block w-full text-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                >
                    + New instance
                </Link>
            </div>
        </div>
    );
}
