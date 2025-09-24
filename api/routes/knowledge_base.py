from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
import tempfile
import os
from pathlib import Path

from ..models.responses import KBUploadResponse, KBStatusResponse, KBUploadResponseWithTenant, KBStatusResponseWithTenant
from ..models.requests import UserRole, DocumentVisibility
from data_ingestion import ingest_file_with_feedback
from echo_ui import get_vector_store_status

router = APIRouter(prefix="/api/v1", tags=["knowledge_base"])

@router.post("/knowledge-base/upload", response_model=KBUploadResponse)
async def upload_files_to_kb(
    files: List[UploadFile] = File(...)
):
    """
    Upload files to knowledge base (legacy endpoint for backward compatibility)
    """
    return await _process_file_upload(files)

@router.post("/knowledge-base/upload-tenant", response_model=KBUploadResponseWithTenant)
async def upload_files_to_kb_with_tenant(
    files: List[UploadFile] = File(...),
    tenant_id: str = Form(default="default"),
    access_roles: List[str] = Form(default=["customer"]),
    document_visibility: str = Form(default="Public")
):
    """
    Upload files to knowledge base with tenant context and RBAC
    """
    # Validate document visibility
    try:
        DocumentVisibility(document_visibility)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid document_visibility. Must be one of: {[v.value for v in DocumentVisibility]}")

    # Validate roles
    valid_roles = []
    for role in access_roles:
        try:
            UserRole(role)
            valid_roles.append(role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role '{role}'. Must be one of: {[r.value for r in UserRole]}")

    # Process files with tenant context
    upload_result = await _process_file_upload(files, tenant_id=tenant_id, access_roles=valid_roles, document_visibility=document_visibility)

    return KBUploadResponseWithTenant(
        tenant_id=tenant_id,
        access_validated=True,
        success=upload_result.success,
        files_processed=upload_result.files_processed,
        chunks_created=upload_result.chunks_created,
        errors=upload_result.errors,
        details=upload_result.details
    )

async def _process_file_upload(
    files: List[UploadFile],
    tenant_id: str = "default",
    access_roles: List[str] = None,
    document_visibility: str = "Public"
) -> KBUploadResponse:
    """
    Common file upload processing logic with tenant context support
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Set default access roles if not provided
    if access_roles is None:
        access_roles = ["customer"]

    # Validate file count (max 5 files)
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed per request")

    results = []
    total_chunks = 0
    errors = []
    successful_files = 0

    # Supported file types
    supported_extensions = {'.pdf', '.docx', '.txt', '.md'}

    for file in files:
        try:
            # Validate file size (10MB limit)
            file_content = await file.read()
            if len(file_content) > 10 * 1024 * 1024:  # 10MB
                error_msg = f"File {file.filename} exceeds 10MB size limit"
                errors.append(error_msg)
                results.append({
                    "file_name": file.filename,
                    "success": False,
                    "message": error_msg,
                    "chunks_created": 0
                })
                continue

            # Validate file type
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in supported_extensions:
                error_msg = f"File {file.filename} has unsupported format: {file_extension}"
                errors.append(error_msg)
                results.append({
                    "file_name": file.filename,
                    "success": False,
                    "message": error_msg,
                    "chunks_created": 0
                })
                continue

            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name

            try:
                # Process file using existing ingestion function with tenant context
                result = ingest_file_with_feedback(
                    tmp_file_path,
                    file.filename,
                    tenant_id=tenant_id,
                    access_roles=access_roles,
                    document_visibility=document_visibility
                )

                if result["success"]:
                    successful_files += 1
                    # Extract chunk count from success message
                    chunks_created = 0
                    if "chunks" in result["message"]:
                        try:
                            # Extract number from message like "Successfully processed 15 chunks"
                            chunks_created = int(result["message"].split()[2])
                            total_chunks += chunks_created
                        except (IndexError, ValueError):
                            chunks_created = 0

                    results.append({
                        "file_name": file.filename,
                        "success": True,
                        "message": result["message"],
                        "chunks_created": chunks_created
                    })
                else:
                    errors.append(f"{file.filename}: {result['message']}")
                    results.append({
                        "file_name": file.filename,
                        "success": False,
                        "message": result["message"],
                        "chunks_created": 0
                    })

            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass

        except Exception as e:
            error_msg = f"Error processing {file.filename}: {str(e)}"
            errors.append(error_msg)
            results.append({
                "file_name": file.filename,
                "success": False,
                "message": error_msg,
                "chunks_created": 0
            })

    # Determine overall success
    overall_success = successful_files > 0 and len(errors) == 0

    return KBUploadResponse(
        success=overall_success,
        files_processed=successful_files,
        chunks_created=total_chunks,
        errors=errors,
        details=results
    )


@router.get("/knowledge-base/status", response_model=KBStatusResponse)
async def get_kb_status():
    """
    Get KB stats and document count (legacy endpoint for backward compatibility)
    Function Mapping: echo_ui.get_vector_store_status()
    """
    try:
        vector_status = get_vector_store_status()

        # Map the response to our API model
        status = vector_status.get("status", "error")
        document_count = vector_status.get("document_count", 0)
        collection_name = vector_status.get("collection_name", "default_collection")
        error_message = vector_status.get("error_message") if status == "error" else None

        return KBStatusResponse(
            status=status,
            document_count=document_count,
            collection_name=collection_name,
            error_message=error_message
        )
    except Exception as e:
        return KBStatusResponse(
            status="error",
            document_count=0,
            collection_name="default_collection",
            error_message=str(e)
        )

@router.get("/knowledge-base/status-tenant", response_model=KBStatusResponseWithTenant)
async def get_kb_status_with_tenant(
    tenant_id: str = "default"
):
    """
    Get KB stats and document count with tenant filtering
    """
    try:
        vector_status = get_vector_store_status(tenant_id=tenant_id)

        # Map the response to our API model
        status = vector_status.get("status", "error")
        document_count = vector_status.get("document_count", 0)
        collection_name = vector_status.get("collection_name", "default_collection")
        error_message = vector_status.get("error_message") if status == "error" else None

        return KBStatusResponseWithTenant(
            tenant_id=tenant_id,
            access_validated=True,
            status=status,
            document_count=document_count,
            collection_name=collection_name,
            error_message=error_message
        )
    except Exception as e:
        return KBStatusResponseWithTenant(
            tenant_id=tenant_id,
            access_validated=False,
            status="error",
            document_count=0,
            collection_name="default_collection",
            error_message=str(e)
        )