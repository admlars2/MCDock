import { Link } from "react-router-dom";
import { useInstances } from "../hooks/useInstances";
import Sidebar from "../components/Sidebar";

export default function Instances() {
    const { data, isLoading, isError } = useInstances();

    return (
        <>
            <Sidebar />
            <div className="p-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {isLoading ? <p className="p-6">Loading servers…</p> : <></>}
                {isError ? <p className="p-6 text-red-600">Failed to load instances.</p> : <></>}
                {data?.map((inst) => (
                    <div
                    key={inst.name}
                    className="rounded-xl border shadow p-4 space-y-2 bg-white"
                    >
                    <h2 className="font-semibold text-lg">{inst.name}</h2>

                    <p>
                        Status:&nbsp;
                        <span
                        className={
                            inst.status === "running"
                            ? "text-green-600"
                            : inst.status === "stopped"
                            ? "text-yellow-600"
                            : "text-gray-600"
                        }
                        >
                        {inst.status}
                        </span>
                    </p>

                    <Link
                        to={`/instances/${inst.name}`}
                        className="inline-block px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                        View
                    </Link>
                    </div>
                ))}
            </div>
        </>
    );
}
